import sublime, sublime_plugin
import os
import glob
import xml.etree.ElementTree as ET
import fnmatch
import re
import sys

tags = []

def debug(string):
    if settings.has("debug_enabled"):
        if settings.get("debug_enabled"):
            print(string)
def plugin_loaded():
    global settings
    settings = sublime.load_settings('TLD_Autocomplete.sublime-settings')
    ns = {}
    debug("Loading TLD Autocomplete v1.0.3")
    del tags[:]
    if settings.has("xml_name_space"):
        ns = {'ns': settings.get("xml_name_space")}
        debug("Name Space found: " + settings.get("xml_name_space"))
    if settings.has("tld_folder_path"):
        debug("TLD Folder Path Found: " + settings.get("tld_folder_path"))
        for files in locate('*.tld',settings.get("tld_folder_path")):
            debug("Processing File: " + files)
            tree = ET.parse(files)
            root = tree.getroot()
            shortName = root.find('ns:short-name', ns).text
            debug("Found Short Name: " + shortName)
            debug("Scanning Tags...")
            for tag in root.findall('ns:tag', ns):
                nameObj = tag.find('ns:name', ns)
                if nameObj is None:
                    continue
                name = nameObj.text

                if isinstance(name, str):
                    debug("Tag - Name:" + name)
                descriptionObj = tag.find('ns:description', ns)
                if descriptionObj is not None:
                    description = descriptionObj.text
                    if isinstance(description, str):
                        debug("Tag - Description: " + description)
                    
                tagAttributes = []
                for attributes in tag.findall('ns:attribute', ns):
                    # Check if the attribute has a name
                    attributeNameObj = attributes.find('ns:name', ns)
                    if attributeNameObj is None:
                        continue
                    attributeName = attributeNameObj.text
                    if isinstance(attributeName, str):
                        debug("Tag - Attribute: " + attributeName)

                    # Check if the attribute is requried or not
                    attributeRequiredObj = attributes.find('ns:required', ns)
                    if attributeRequiredObj is None:
                        attributeRequired = False
                    else:
                        if attributeRequiredObj.text == "true":
                            attributeRequired = True
                        else:
                            attributeRequired = False

                    if attributeRequired:
                        debug("Tag - Required: True")
                    else:
                    	debug("Tag - Required: False")
                    # Create an attribute object
                    attribute = Attribute(attributeName, attributeRequired)

                    # Check if the attribute has possible-values array inside of it
                    possibleValues = attributes.find('ns:possible-values', ns)
                    if possibleValues is not None:
                        for possibleValue in possibleValues.findall('ns:possible-value', ns):
                            attribute.addPossibleValue(possibleValue.text);
                            debug("Tag - Possible Value: " + possibleValue.text)
                            
                    tagAttributes.append(attribute)
                tags.append(Tag(shortName,name,description,tagAttributes))
        debug("Parsing Complete!")
def locate(pattern,root=os.curdir):
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files,pattern):
            yield os.path.join(path,filename)

plugin_loaded()

class ShortNameTagCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        debug("Performing Autocomplete")
        if(view.match_selector(locations[0], "text.html.jsp")):
            # Get current word & line
            word_bounds = view.word(locations[0])
            line_bounds = view.line(locations[0])

            # Get line to current cursor
            prefix_bounds = sublime.Region(line_bounds.begin(), word_bounds.begin())
            line_to_current = view.substr(prefix_bounds)

            # Previous character
            ch = view.substr(sublime.Region(locations[0] - 1, locations[0]))
            debug("Previous Character: " + ch)

            # List of autocompletes to return
            autoCompletion = []

            if (ch == '"' or ch == '\''):
                # This will be true if we're inside attribute field
                open_tag_index = line_to_current.rfind('<') + 1
                if open_tag_index != -1:
                    currentTag = view.substr(view.word(line_bounds.begin() + open_tag_index))
                    debug("Current Tag: " + currentTag)
                    currentSubTag = view.substr(view.word(line_bounds.begin() + open_tag_index + len(currentTag) + 1))
                    debug("Current Sub-tag: " + currentTag)
                    attribute = view.substr(view.word(locations[0] - 2))
                    debug("Current Attribute: " + currentTag)
                    for tag in tags:
                        if currentTag == tag.shortName and currentSubTag == tag.name:
                            for tagAttribute in tag.attributes:
                                if attribute == tagAttribute.name:
                                    for possibleValue in tagAttribute.possibleValues:
                                        debug("Possible Value: " + possibleValue)
                                        preparedTag = [possibleValue + "\tValue", possibleValue]
                                        autoCompletion.append(preparedTag)
                debug("Autocomplete has finished with " + str(len(autoCompletion)) +" results!")
                return (autoCompletion, sublime.INHIBIT_WORD_COMPLETIONS)
            if (ch == ' '):
                # This will be true if we're inside a tag
                open_tag_index = line_to_current.rfind('<') + 1
                if open_tag_index != -1:
                    currentTag = view.substr(view.word(line_bounds.begin() + open_tag_index))
                    debug("Current Tag: " + currentTag)
                    currentSubTag = view.substr(view.word(line_bounds.begin() + open_tag_index + len(currentTag) + 1))
                    debug("Current Sub-tag: " + currentTag)
                    for tag in tags:
                        if currentTag == tag.shortName and currentSubTag == tag.name:
                            for tagAttribute in tag.attributes:
                                if tagAttribute.required:
                                    preparedTag = [tagAttribute.name + "\tAttribute [Required]", tagAttribute.name + "=\"$0\" "]
                                else:
                                    preparedTag = [tagAttribute.name + "\tAttribute", tagAttribute.name + "=\"$0\" "]
                                debug("Attribute: " + tagAttribute.name)
                                autoCompletion.append(preparedTag)
                debug("Autocomplete has finished with " + str(len(autoCompletion)) +" results!")
                return (autoCompletion)
            elif(ch == '<'):
                # This will be true if we're about to declare a tag
                for tag in tags:
                    debug("Tag: " + tag.shortName + ":" + tag.name)
                    preparedTag = [tag.shortName + ":" + tag.name + "\tTaglib", tag.shortName + ":" + tag.name + " $0></" + tag.shortName + ":" + tag.name + ">"]
                    autoCompletion.append(preparedTag)
                debug("Autocomplete has finished with " + str(len(autoCompletion)) +" results!")
                return (autoCompletion)
            elif(ch == ':'):
                # This will be true if we're about to declare a subtag
                open_tag_index = line_to_current.rfind('<') + 1
                if open_tag_index != -1:
                    currentTag = view.substr(view.word(line_bounds.begin() + open_tag_index))
                    debug("Current Tag: " + currentTag)
                    for tag in tags:
                        if currentTag == tag.shortName:
                            debug("Sub-tag: " + tag.shortName + ":" + tag.name)
                            preparedTag = [tag.shortName + ":" + tag.name + "\tTaglib", tag.shortName + ":" + tag.name + " $0></" + tag.shortName + ":" + tag.name + ">"]
                            autoCompletion.append(preparedTag)
                debug("Autocomplete has finished with " + str(len(autoCompletion)) +" results!")
                return (autoCompletion)
            else:
                debug("Autocomplete has finished with no results!")
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