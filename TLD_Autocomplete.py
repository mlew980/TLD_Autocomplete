import sublime, sublime_plugin
import os
import glob
import xml.etree.ElementTree as ET
import fnmatch
import re
import sys

tags =[]
maxTagLength =0
def plugin_loaded():
    global maxTagLength
    global settings
    settings = sublime.load_settings('TLD_Autocomplete.sublime-settings')
    ns = {}
    if settings.has("xml_name_space"):
        ns = {'ns': settings.get("xml_name_space")}
    if settings.has("tld_folder_path"):
        for files in locate('*.tld',settings.get("tld_folder_path")):
            tree = ET.parse(files)
            print(files)
            root = tree.getroot()
            shortName = root.find('ns:short-name', ns).text
            for tag in root.findall('ns:tag', ns):
                name = tag.find('ns:name', ns).text
                description = tag.find('ns:description', ns).text
                if (len(shortName + ":" + name) > maxTagLength):
                    maxTagLength = len(shortName + ":" + name)
                tagAttributes = []
                for attributes in tag.findall('ns:attribute', ns):
                    tagAttributes.append(attributes.find('ns:name', ns).text)
                tags.append(Tag(shortName,name,description,tagAttributes))

def locate(pattern,root=os.curdir):
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files,pattern):
            yield os.path.join(path,filename)

class ShortNameTagCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if(view.match_selector(locations[0], "text.html meta.tag")):
            pt = locations[0] - len(prefix) - 1
            ch = view.substr(sublime.Region(pt, pt + 1))
            autoCompletion = []
            if (ch == ' '):
                currentLine = view.substr(view.line(view.sel()[0].begin()))
                for tag in tags:
                    if currentLine.find(tag.shortName + ":" + tag.name + " ") != -1:
                        for tagAttribute in tag.attributes:
                            preparedTag = [tagAttribute + "\tAttribute", tagAttribute + "=\"\""]
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