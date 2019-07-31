import sublime, sublime_plugin
import os
import glob
import xml.etree.ElementTree as ET
import fnmatch
import re
import sys

tags = []
maxTagLength =0
def plugin_loaded():
    global maxTagLength
    global settings
    settings = sublime.load_settings('TLD_Autocomplete.sublime-settings')
    ns = {}
    del tags[:]
    if settings.has("xml_name_space"):
        ns = {'ns': settings.get("xml_name_space")}
    if settings.has("tld_folder_path"):
        for files in locate('*.tld',settings.get("tld_folder_path")):
            tree = ET.parse(files)
            root = tree.getroot()
            shortName = root.find('ns:short-name', ns).text
            for tag in root.findall('ns:tag', ns):
                nameObj = tag.find('ns:name', ns)
                if nameObj is None:
                    continue
                name = nameObj.text
                descriptionObj = tag.find('ns:description', ns)
                if descriptionObj is None:
                    continue
                description = descriptionObj.text
                if (len(shortName + ":" + name) > maxTagLength):
                    maxTagLength = len(shortName + ":" + name)
                tagAttributes = []
                for attributes in tag.findall('ns:attribute', ns):
                    # Check if the attribute has a name
                    attributeNameObj = attributes.find('ns:name', ns)
                    if attributeNameObj is None:
                        continue
                    attributeName = attributeNameObj.text

                    # Check if the attribute is requried or not
                    attributeRequiredObj = attributes.find('ns:required', ns)
                    if attributeRequiredObj is None:
                        attributeRequired = False
                    else:
                        if attributeRequiredObj.text == "true":
                            attributeRequired = True
                        else:
                            attributeRequired = False

                    # Create an attribute object
                    attribute = Attribute(attributeName, attributeRequired)

                    # Check if the attribute has possible-values array inside of it
                    possibleValues = attributes.find('ns:possible-values', ns)
                    if possibleValues is not None:
                        for possibleValue in possibleValues.findall('ns:possible-value', ns):
                            attribute.addPossibleValue(possibleValue.text);
                            
                    tagAttributes.append(attribute)

                tags.append(Tag(shortName,name,description,tagAttributes))
def locate(pattern,root=os.curdir):
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files,pattern):
            yield os.path.join(path,filename)

plugin_loaded()

class ShortNameTagCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if(view.match_selector(locations[0], "text.html.jsp")):
            pt = locations[0] - len(prefix) - 1
            ch = view.substr(sublime.Region(pt, pt + 1))
            autoCompletion = []
            if (ch == '"'):
                pt = locations[0] - len(prefix) - 2
                attribute = view.substr(view.word(pt))
                currentSubTag = view.substr(view.word(pt - len(attribute) - 1))
                currentTag = view.substr(view.word((pt - len(attribute) - 1) - len(currentSubTag) - 1))
                for tag in tags:
                    if currentTag == tag.shortName and currentSubTag == tag.name:
                        for tagAttribute in tag.attributes:
                            for possibleValue in tagAttribute.possibleValues:
                                preparedTag = [possibleValue + "\tValue", possibleValue]
                                autoCompletion.append(preparedTag)
                return (autoCompletion, sublime.INHIBIT_WORD_COMPLETIONS)
            if (ch == ' '):
                currentSubTag = view.substr(view.word(pt))
                currentTag = view.substr(view.word(pt - len(currentSubTag) - 1))
                for tag in tags:
                    if currentTag == tag.shortName and currentSubTag == tag.name:
                        for tagAttribute in tag.attributes:
                            if tagAttribute.required:
                                preparedTag = [tagAttribute.name + "\tAttribute [Required]", tagAttribute.name + "=\"$0\""]
                            else:
                                preparedTag = [tagAttribute.name + "\tAttribute", tagAttribute.name + "=\"$0\""]
                            autoCompletion.append(preparedTag)
                return (autoCompletion)
            elif(ch == '<'):
                for tag in tags:
                    preparedTag = [tag.shortName + ":" + tag.name + "\tTaglib", tag.shortName + ":" + tag.name + " $0></" + tag.shortName + ":" + tag.name + ">"]
                    autoCompletion.append(preparedTag)
                return (autoCompletion)
            else:
                return []
        else:
            return []

class Tag:
    def __init__(self, shortName, name, description, attributes):
        self.shortName = shortName
        self.name = name
        self.description = description
        self.attributes = attributes

class Attribute:
    def __init__(self, name, required):
        self.name = name
        self.required = required
        self.possibleValues = []
    def addPossibleValue(self, value):
        self.possibleValues.append(value)