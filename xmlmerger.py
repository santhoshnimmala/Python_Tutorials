import sys
import os
from lxml import etree as le
import xml.etree.cElementTree  as ET
from ReleaseTool.templates import *
import time
from ReleaseTool.addons import *
import re

"""
 Name : Nimmala Naga Santhosh Baba & Venky Ravisekar
 jira : RTSMST-2952 & RTSMST-3014
 

 ...

 Parameters
 ----------
 args[1]  : str
     a formatted string that is usually "merge" 
 args[2] : str
     folder Path for XML files 
args[3]: str
     name of the merged Cmf template 
args[4]: str
     Release.txt - a file consisting of the list of Jira's to filter by
args[3]: str
     a formatted string that is usually "Release"
 """

# we are using two list one for xml objects and another for  Tracking the uniq xml elements
t = time.localtime()
timestamp = time.strftime('%d%b%Y', t)
xml_data = []  # we need this for uniq xml elements with parent elements copied in list
xml_names = []  # storing xml objects names
jira_list = []  # jira list
select_list = []  # selective xml List
group_list = []  # to store elements belongs to group this takes input from config.txt
orchestrator_seq =[]


# extracting jira numbers from file passed to function , file should present in folder
def jira_extract(dir, filename):
    file = filename
    Jira_file_name = os.path.join(dir, file)
    xml_files_list = os.listdir(dir)
    with open(Jira_file_name, 'r') as f:
        lines= f.read()
        intake_files = [line for line in lines.split(',')]
        for i in intake_files:
            if i.startswith(i) and i.endswith('.xml'):
                jira_list.append(i.lstrip())
        print("taking this file to list %s" % (i))
    print(jira_list)

    return jira_list


# getting all the valid files from dir and doing some magic and writing back to release.xml
def generate_release(dir, filename):
    if os.path.isfile(os.path.join(dir, filename)):
        files = jira_extract(dir, filename)
    else:
        files = list_of_files(dir)

    for filename in files:
        if not '.xml' in filename: continue
        fullname = os.path.join(dir, filename)
        root = le.parse(fullname)
        for configitem in root.findall('.//configuration-item'):  # taking all config-items form xmls and looping over
            for instances in configitem.findall('.//instances'):
                if (len(instances) > 0):  # atleast one instance should be there
                    generate_instances(configitem,
                                       instances)  # which checks for duplicate cm elements and takes only uniqe


# once config item we got from generatexml we will look for instances and from instances we will pick instance
def generate_instances(configItem, instancesElementsList):
    for instanceItem in instancesElementsList.findall('.//instance'):
        item = XmlObject()  # calling xmlobject from class XmlObject
        item.CM = configItem.attrib['object-id']
        item.name = item.CM + instanceItem.attrib['label']
        item.data = copy_with_parent(instanceItem)
        item.data = le.fromstring(le.tostring(item.data, xml_declaration=True,
                                              encoding=item.data.getroottree().docinfo.encoding,
                                              doctype=item.data.getroottree().docinfo.doctype)).getroottree()

        if item.name in xml_names:
            pass
        else:
            xml_data.append(item)  # appending elements to list
        xml_names.append(item.name)  # appending xml names to list just to keep track of xml we are writing back


# this used to copy the parent tree
def copy_with_parent(elem):
    docinfo = elem.getroottree().docinfo

    result = le.fromstring(le.tostring(elem, xml_declaration=True, encoding=docinfo.encoding, doctype=docinfo.doctype))
    parent = elem.getparent()

    while parent is not None:
        just_parent_elem = copy_parent(parent)  # we just want the element and its attributes
        just_parent_elem.insert(1, result)
        result = just_parent_elem

        parent = parent.getparent()  # move up to next parent

    return result


# once we got all uniq object from list this function will assemble all the elements
def assemble_files(cmf):
    root = le.XML(rootelement(cmf))
    for item in xml_data:

        xml = item.data
        configuration_item_elems = xml.findall('.//configuration-item')
        assert (len(configuration_item_elems) > 0)

        for configurationItemElemToAdd in configuration_item_elems:
            if not find_configitem_insert_instances(root, configurationItemElemToAdd):
                print(">Copying across %s" % configurationItemElemToAdd.attrib['object-id'])
                root.append(configurationItemElemToAdd)
        print(le.tostring(root, encoding='utf8').decode('utf8'))
    with open('release.xml', 'wb') as f:  # writing all the content into single file
        f.write(le.tostring(root, pretty_print=True, xml_declaration=True, encoding='utf8'))


# this function will be used to right place to insert  the element
def find_configitem_insert_instances(root, configurationItemElemToAdd):
    assert (configurationItemElemToAdd.attrib['object-id'] is not None)

    for targetConfigItem in root.getchildren():
        assert (targetConfigItem.attrib['object-id'] is not None)
        if targetConfigItem.attrib['object-id'] == configurationItemElemToAdd.attrib['object-id']:
            for sourceChildInstances in configurationItemElemToAdd.getchildren():
                print(">Merging %s (%s instances)" % (
                    targetConfigItem.attrib['object-id'], len(sourceChildInstances.getchildren())))
                for instanceToAdd in sourceChildInstances.getchildren():
                    targetConfigItem.find("instances").append(instanceToAdd)
            return True
    return False


# copy the parent element
def copy_parent(elem):
    newelem = elem.makeelement(elem.tag, elem.attrib, elem.nsmap)  # note we preserve the WF
    newelem.text = elem.text
    newelem.tail = elem.tail
    return newelem


# listing all the files with valid xml files from Directory
def list_of_files(dir):
    files = []
    for file in os.listdir(dir):
        if not file.endswith('.xml'): continue
        fullname = os.path.join(dir, file)
        files.append(fullname)
    return files


# Stripping Release Xml to individual CM's xmls
def stripping_into_cms(dir):
    filename = 'release.xml'
    full_name = os.path.join(dir, filename)

    if os.path.exists(os.path.isfile(filename)):
        try:
            os.makedirs(PATH1)
            os.makedirs(PATH_TO_PACK)
            print(PATH_TO_PACK)
        except OSError:
            print("Creation of the directory %s failed" % PATH1)
        else:
            print("Successfully created the directory %s and %s " % (PATH1,PATH_TO_PACK))
    root = le.parse(filename)
    for configitem in root.findall('.//configuration-item'):
        assert (len(configitem) > 0)
        cm_name = configitem.attrib['object-id']
        root1 = le.XML(rootelement(cm_name))
        root1.append(configitem)
        complete_path = os.path.join(PATH1, cm_name) + '.xml'
        with open(complete_path, "wb") as f:
            f.write(le.tostring(root1, pretty_print=True, xml_declaration=True, encoding='utf8'))


# just tells how to use
def usage(usage):
    print("Help for {0}".format(usage))
    print("--------------------------------------")
    print("Merging xmls Please give the folder of Release Xmls ")
    print("unpack <folder path containing Xmls>")
    print("\n[merging xmls]")
    exit(1)


'''Release part this will do the Getting all Requried xml from CM.xmls files  and generating JIRA%s with date folder and to_pack folder with xmls and '''


# function will segregate elements belongs to selective or group takes input file from config/config.txt
def selective_or_group(dir, filename):
    file = filename
    jira_file_name = os.path.join(dir, file)
    with open(jira_file_name, 'r') as f:
        for line in f:
            split = line.split(';')
            orchestrator_seq.append(split[1])
            selective = {}
            group = {}
            if split[2] == 'Selective':
                selective[split[1]] = split[3].rstrip('\n').split(',')
                select_list.append(selective)
            elif split[2] == 'Group':
                group[split[1]] = split[3].rstrip('\n').split(',')
                group_list.append(group)
            print("taking this file to list %s" % (line))
        print(select_list)
        print(group_list)
        print(orchestrator_seq)


# generating list of cms with filename which goes to selective xmls in to_pack folder
def generate_selective(dir):
    for index in range(len(select_list)):
        for key in select_list[index]:
            root1 = le.XML(rootelement(key))
            temp = []
            module_files = select_list[index][key]
            for filename in module_files:
                cm = filename
                filename =  PATH1 + '\\' + filename + '.xml'
                fullname = os.path.join( filename)
                if os.path.isfile(fullname):
                    temp.append(cm)
                    root = le.parse(fullname)
                    xml = root
                    configurationItemElems = xml.findall('.//configuration-item')
                    assert (len(configurationItemElems) > 0)
                    for i in configurationItemElems:
                        root1.append(i)
                    print(le.tostring(root1, encoding='utf8').decode('utf8'))
            select_list[index][key] = temp

        full_path = os.path.join(PATH_TO_PACK, key) + '.xml'
        instance_present = root1.findall('.//instances')
        if len(instance_present) > 0:
            with open(full_path, 'wb') as f:  # writing all the content into single file
                f.write(le.tostring(root1, pretty_print=True, xml_declaration=True, encoding='utf8'))
                f.close()
    print(select_list)
    generate_group(dir)


#generating Orchestration for groups which executes through group parameter
def generate_group(dir):
    for index in range(len(group_list)):
        for key in group_list[index]:
            temp = []
            module_files = group_list[index][key]
            for filename in module_files:
                cm = filename
                filename = PATH1 + '\\' + filename + '.xml'
                fullname = os.path.join(filename)
                if os.path.isfile(fullname):
                    temp.append(cm)
                else:
                    print(" cm is not present %s" % cm)
        group_list[index][key] = temp
    print(group_list)
    generate_orchestrator(dir)


#replacing special chars
def replace_characters_list(listString):
    return str(listString).replace('[', '').replace(']', '').replace("'", "").replace(' ', '')

# generating orchestrator file in to_pack folder
def generate_orchestrator(dir):
    group_list_dict = dict((key, ele[key]) for ele in group_list for key in ele)
    select_list_dict = dict((key, d[key]) for d in select_list for key in d)
    full_path = os.path.join(PATH_TO_PACK, 'Orchestrator') + '.txt'
    print("writing Orchestrator to path %s" % full_path)
    with open(full_path, 'w+') as q:
        for i in orchestrator_seq:
            if i in group_list_dict:
                module_files = replace_characters_list(group_list_dict[i])
                if len(module_files) == 0:
                    pass
                else:
                    Group_str = 'Group ; %s; %s' % (i, module_files)
                    q.write(Group_str)
                    q.write('\n')
            elif i in select_list_dict:
                module_files = replace_characters_list(select_list_dict[i])
                if len(module_files) == 0:
                    pass
                else:
                    sel_str = 'Selective ; %s; %s' % (i, module_files)
                    q.write(sel_str)
                    q.write('\n')
    q.close()



'''Main section'''
if __name__ == '__main__':
    args = sys.argv
    prog = os.path.basename(args[0])
    # Help call
    if '-h' in args or '--help' in args or len(args) < 2:
        usage(prog)
    t = time.localtime()
    timestamp = time.strftime('%d%b%Y', t)
    if len(sys.argv) >= 7:
        PATH1 = (args[6]) # path for jira folder with Date if they give parameter
        PATH_TO_PACK = (os.path.join(args[6],'Topack'))# path folder for to_pack folder if they give parameter
    else:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        PATH1 = (dir_path+'/JIRA')  # path for jira folder with Date
        PATH_TO_PACK = (PATH1+'/Topack')  # path folder for to_pack folder
    print(" Path to generate the CM %s"%PATH1)
    print(" path to pack %s"%PATH_TO_PACK)
    if args[1] == "merge":
        if len(args) < 2: usage(prog)
        generate_release(args[2], args[4])
        assemble_files(args[3])
        stripping_into_cms(args[2])
        print(xml_names)
        print(xml_data)
    if args[5] == "Release":
        selective_or_group('config', 'config.txt')
        generate_selective(args[2])

