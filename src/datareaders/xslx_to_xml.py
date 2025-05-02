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

    # Safely get values with fallback to empty strings
    title = str(paperData.title) if pd.notna(paperData.title) else ""
    batch = str(paperData.batch) if pd.notna(paperData.batch) else ""
    rescode = str(paperData.rescode) if pd.notna(paperData.rescode) else ""
    authors_raw = str(paperData.authors) if pd.notna(paperData.authors) else ""
    advisers_raw = str(paperData.advisers) if pd.notna(paperData.advisers) else ""
    keywords_raw = str(paperData.keywords) if pd.notna(paperData.keywords) else ""

    # Set paper node attribs
    paper = ET.SubElement(root, "paper")
    paper.set("title", title)
    paper.set("rescode", batch[:-2] + "_" + rescode if len(batch) >= 2 else "_" + rescode)

    # Separate authors and advisers
    authors = authors_raw.split(", ") if authors_raw else []
    advisers = advisers_raw.split(", ") if advisers_raw else []

    for a in authors:
        author = ET.SubElement(paper, "author")
        author.text = a

    for a in advisers:
        adviser = ET.SubElement(paper, "adviser")
        adviser.text = a

    # Separate keywords
    keywords = keywords_raw.split(", ") if keywords_raw else []

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