# ephemera
# Convert xlsx into xml

# import
import xml.etree.ElementTree as ET # XML
import xml.dom.minidom as minidom # Format XML
import pandas as pd # Pandas

# Take input
excelFPath = input("Please enter filepath to xlsx file:")

# Import data using panda
print("reading excel file...")
data = pd.read_excel(excelFPath)

# Make xml
root = ET.Element("data")

for i in range(len(data)):
    # Get paper data
    paperData = data.loc[i]

    # Set paper node attribs
    paper = ET.SubElement(root, "paper")
    paper.set("title", paperData.title)
    paper.set("rescode", str(paperData.batch) + "_" + paperData.rescode)

    # Separate authors and advisers
    authors = paperData.authors.split(", ")
    advisers = paperData.advisers.split(", ")

    for a in authors:
        author = ET.SubElement(paper, "author")
        author.text = a

    for a in advisers:
        adviser = ET.SubElement(paper, "adviser")
        adviser.text = a

    # Separate keywords
    keywords = paperData.keywords.split(", ")

    for k in keywords:
        keyword = ET.SubElement(paper, "keyword")
        keyword.text = k
    
# Convert to a string and format it with indentation
xmlStr = ET.tostring(root, encoding="utf-8")
parsedXML = minidom.parseString(xmlStr)
formattedXML = parsedXML.toprettyxml(indent="  ")

# Write to a file
with open("output.xml", "w", encoding="utf-8") as f:
    f.write(formattedXML)