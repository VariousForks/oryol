'''
Code generator for message protocol xml files.
'''

import os

#-------------------------------------------------------------------------------
def writeHeaderTop(f, xmlRoot) :
    '''
        Write header area for the generated C++ header.
    '''
    f.write('#pragma once\n')
    f.write('//-----------------------------------------------------------------------------\n')
    f.write('/*\n')
    f.write('    machine generated, do not edit!\n')
    f.write('*/\n')

#-------------------------------------------------------------------------------
def writeIncludes(f, xmlRoot) :
    '''
        Write include statements in the generated C++ header.
    '''
    f.write('#include "Messaging/Message.h"\n')
    f.write('#include "Messaging/Serializer.h"\n')
    parentHdr = xmlRoot.get('parenthdr', 'Messaging/MessageProtocol.h')
    f.write('#include "{}"\n'.format(parentHdr))

    for hdr in xmlRoot.findall('Header') :
        f.write('#include "{}"\n'.format(hdr.get('path')))
    f.write('\n')

#-------------------------------------------------------------------------------
def writeMessageIdEnum(f, xmlRoot) :
    '''
    Write the enum with message ids
    '''
    parentNameSpace = xmlRoot.get('parent', 'MessageProtocol')

    f.write('class MessageId {\n')
    f.write('public:\n')
    f.write('    enum {\n')
    msgCount = 0
    for msg in xmlRoot.findall('Message') :
        if msgCount == 0:
            f.write('        ' + msg.get('name') + 'Id = ' + parentNameSpace + '::MessageId::NumMessageIds, \n')
        else :
            f.write('        ' + msg.get('name') + 'Id,\n')
        msgCount += 1
    f.write('        NumMessageIds\n')
    f.write('    };\n')
    f.write('    static const char* ToString(Messaging::MessageIdType c) {\n')
    f.write('        switch (c) {\n')
    for msg in xmlRoot.findall('Message') :
        msgName = msg.get('name') + 'Id'
        f.write('            case ' + msgName + ': return "' + msgName + '";\n')
    f.write('            default: return "InvalidMessageId";\n')
    f.write('        }\n')
    f.write('    };\n')
    f.write('    static Messaging::MessageIdType FromString(const char* str) {\n')
    for msg in xmlRoot.findall('Message') :
        msgName = msg.get('name') + 'Id'
        f.write('        if (std::strcmp("' + msgName + '", str) == 0) return ' + msgName + ';\n')
    f.write('        return Messaging::InvalidMessageId;\n')
    f.write('    };\n')
    f.write('};\n')

#-------------------------------------------------------------------------------
def getAttrDefaultValue(attr) :
    '''
    Get the default value for a given attribute
    '''
    defValue = attr.get('def')
    attrType = attr.get('type')
    if attrType in ('int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64') :
        if not defValue :
            defValue = '0'
    elif attrType in ('char', 'unsigned char', 'int', 'unsigned int', 'short', 'unsigned short', 'long', 'unsigned long') :
        if not defValue :
            defValue = '0'
    elif attrType in ('float32', 'float') :
        if not defValue :
            defValue = '0.0f'
    elif attrType in ('float64', 'double') :
        if not defValue :
            defValue = '0.0'
    return defValue;

#-------------------------------------------------------------------------------
def getRefType(attrType) :
    '''
    Get the reference type string for an attribute type
    ''' 
    if attrType in ('int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64') :
        return attrType
    elif attrType in ('char', 'unsigned char', 'int', 'unsigned int', 'short', 'unsigned short', 'long', 'unsigned long') :
        return attrType
    elif attrType in ('float32', 'float') :
        return attrType
    elif attrType in ('float64', 'double') :
        return attrType
    else :
        return 'const ' + attrType + '&'

#-------------------------------------------------------------------------------
def getValueType(attrType) :
    '''
    Get the value type string for an attribute type
    ''' 
    return attrType

#-------------------------------------------------------------------------------
def writeMessageClasses(f, xmlRoot) :
    '''
    Write the message classes to the generated C++ header
    '''
    for msg in xmlRoot.findall('Message') :
        msgClassName = msg.get('name')
        msgParentClassName = msg.get('parent', 'Messaging::Message')
        f.write('class ' + msgClassName + ' : public ' + msgParentClassName + ' {\n')
        poolSize = msg.get('poolSize', '0')
        if int(poolSize) > 0 :
            f.write('    OryolClassPoolAllocDecl(' + msgClassName + ', ' + poolSize + ');\n')
        else :
            f.write('    OryolClassDecl(' + msgClassName + ');\n')
        f.write('public:\n')

        # write constructor
        f.write('    ' + msgClassName + '() {\n')
        f.write('        this->msgId = MessageId::' + msgClassName + 'Id;\n')
        for attr in msg.findall('Attr') :
            attrName = attr.get('name').lower()
            defValue = getAttrDefaultValue(attr)
            if defValue :
                f.write('        this->' + attrName + ' = ' + defValue + ';\n')
        f.write('    };\n')

        # write setters/getters
        for attr in msg.findall('Attr') :
            attrName = attr.get('name')
            attrType = attr.get('type')
            f.write('    void Set' + attrName + '(' + getRefType(attrType) + ' val) {\n')
            f.write('        this->' + attrName.lower() + ' = val;\n')
            f.write('    };\n')
            f.write('    ' + getRefType(attrType) + ' Get' + attrName + '() const {\n')
            f.write('        return this->' + attrName.lower() + ';\n')
            f.write('    };\n')

        # write members
        f.write('private:\n')
        for attr in msg.findall('Attr') :
            attrName = attr.get('name').lower()
            attrType = attr.get('type')
            f.write('    ' + getValueType(attrType) + ' ' + attrName + ';\n')
        f.write('};\n')

#-------------------------------------------------------------------------------
def generateHeader(xmlTree, absHeaderPath) :
    '''
    Generate the C++ header file 
    '''
    xmlRoot = xmlTree.getroot()
    f = open(absHeaderPath, 'w')

    nameSpace = xmlRoot.get('name', 'Messaging')

    writeHeaderTop(f, xmlRoot) 
    writeIncludes(f, xmlRoot)
    f.write('namespace Oryol {\n')
    f.write('namespace ' + nameSpace + ' {\n')
    writeMessageIdEnum(f, xmlRoot)
    writeMessageClasses(f, xmlRoot)
    f.write('}\n')
    f.write('}\n')
    f.close()

#-------------------------------------------------------------------------------
def writeSourceTop(f, xmlRoot, absSourcePath) :
    '''
    Write source file header area
    '''
    path, hdrFileAndExt = os.path.split(absSourcePath)
    hdrFile, ext = os.path.splitext(hdrFileAndExt)

    f.write('//-----------------------------------------------------------------------------\n')
    f.write('// machine generated, do not edit!\n')
    f.write('//-----------------------------------------------------------------------------\n')
    f.write('#include "Pre.h"\n')
    f.write('#include "' + hdrFile + '.h"\n')
    f.write('\n')

#-------------------------------------------------------------------------------
def generateSource(xmlTree, absSourcePath) :
    '''
    Generate the C++ source file
    '''
    xmlRoot = xmlTree.getroot()
    nameSpace = xmlRoot.get('name', 'Messaging')

    f = open(absSourcePath, 'w')
    writeSourceTop(f, xmlRoot, absSourcePath)
    f.write('namespace Oryol {\n')
    f.write('namespace ' + nameSpace + ' {\n')
    for msg in xmlRoot.findall('Message') :
        msgClassName = msg.get('name')
        poolSize = msg.get('poolSize', '0')
        if int(poolSize) > 0 :
            f.write('    OryolClassPoolAllocImpl(' + msgClassName + ', ' + poolSize + ');\n')
        else :
            f.write('    OryolClassImpl(' + msgClassName + ');\n')
    f.write('}\n')
    f.write('}\n')
    f.close()

#-------------------------------------------------------------------------------
def generate(xmlTree, absXmlPath, absSourcePath, absHeaderPath) :
    generateHeader(xmlTree, absHeaderPath)
    generateSource(xmlTree, absSourcePath)
