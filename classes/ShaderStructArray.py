
from DebugObject import DebugObject
from panda3d.core import PTAInt, PTAFloat, PTAMat4
from panda3d.core import PTALVecBase2f, PTALVecBase3f


class ShaderStructElement:

    """ Classes which should be passed to a ShaderStructArray have
    to be subclasses of this class """

    @classmethod
    def getExposedAttributes(self):
        """ Subclasses should implement this method, and return a
        dictionary of values to expose to the shader. A sample 
        return value might be:

        return {
            "someVector": "vec3",
            "someColor": "vec3",
            "someInt": "int",
            "someFloat": "float",
            "someArray": "array<int>(6)",
        }

        All keys have to be a property of the current instance. Arrays
        have to be a PTAxxx, e.g. PTAInt for an int array.

        NOTICE: Currently only int arrays of size 6 are supported, until
        I implement a more general system. """

        raise NotImplementedError()

    def __init__(self):
        """ Constructor, creates the list of referenced lists """

        self.referencedLists = []

    def onPropertyChanged(self):
        """ This method should be called by the class instance itself
        whenever it modifyed an exposed value """

        for structArray in self.referencedLists:
            structArray.objectChanged(self)

    def addListReference(self, structArray):
        """ A struct array calls this when this object is contained
        in the array. """

        if structArray not in self.referencedLists:
            self.referencedLists.append(structArray)

    def removeListReference(self, structArray):
        """ A struct array calls this when this object got deleted from
        the list, e.g. by assigning another object at that index """

        if structArray in self.referencedLists:
            self.referencedLists.remove(structArray)

class ShaderStructArray(DebugObject):

    """ This class provides the ability to pass python lists
    as shader inputs, as panda3d lacks this feature (yet). The 
    items are set with the [] operator. 

    NOTICE the the shader inputs for an object are only refreshed
    when using the [] operator. So whenever you change a property
    of an object, you have to call myShaderStructArray[index] = Object,
    regardless wheter the object is already in the list or not. 

    For further information about accessing the data in your shaders, see
    bindTo()

    Todo: Make the arrays more general. See getExposedAttributes in
    ShaderStructElement.
    """

    def __init__(self, classType, numElements):
        """ Constructs a new array, containing elements of classType and
        with the size of numElements. classType and numElements can't be
        changed after initialization """

        DebugObject.__init__(self, "ShaderStructArray")

        self.debug("Init array, size =", numElements, ", from", classType)
        self.classType = classType
        self.attributes = classType.getExposedAttributes()

        self.size = numElements
        self.parents = {}
        self.ptaWrappers = {}
        self.assignedObjects = [None for i in xrange(numElements)]

        for name, attrType in self.attributes.items():
            arrayType = PTAFloat
            numElements = 1

            if attrType == "mat4":
                arrayType = PTAMat4

            elif attrType == "int":
                arrayType = PTAInt

            # hacky, but works, will get replaced later by a parser
            elif attrType == "array<int>(6)":
                arrayType = PTAInt
                numElements = 6

            elif attrType == "float":
                arrayType = PTAFloat

            elif attrType == "vec2":
                arrayType = PTALVecBase2f

            elif attrType == "vec3":
                arrayType = PTALVecBase3f

            self.ptaWrappers[name] = [
                arrayType.emptyArray(numElements) for i in xrange(self.size)]

    def bindTo(self, parent, uniformName):
        """ In order for an element to recieve this array as an
        shader input, you have to call bindTo(object, uniformName). The data
        will then be available as uniform with the name uniformName in the 
        shader. You still have to define a structure in your shader which has
        the same properties than your objects. As example, if you have the
        following class:

            class Light(ShaderStructElement):
                def __init__(self):
                    ShaderStructElement.__init__(self)
                    self.color = Vec3(1)

                @classmethod
                def getExposedAttributes(self):
                    return {
                        "color": "vec3"
                    }

        you have to define the following structure in your shader:

            struct Light {
                vec3 color;
            }

        and declare the uniform input as:

            uniform Light uniformName[size]


        You can then access the data as with any other uniform input.
        """

        self.parents[parent] = uniformName

        for index in xrange(self.size):
            for attrName, attrType in self.attributes.items():
                inputName = uniformName + \
                    "[" + str(index) + "" "]" + "." + attrName
                inputValue = self.ptaWrappers[attrName][index]

                parent.setShaderInput(inputName, inputValue)

    def objectChanged(self, obj):
        """ A list object calls this when it changed. Do not call this
        directly """
        if obj in self.assignedObjects:
            self[self.assignedObjects.index(obj)] = obj

    def __setitem__(self, index, value):
        """ Sets the object at index to value. This directly updates the 
        shader inputs. """

        if index < 0 or index >= self.size:
            raise Exception("Out of bounds!")

        oldObject = self.assignedObjects[index]

        # Remove old reference
        if value != None and oldObject != None and oldObject != value:
            self.assignedObjects[index].removeListReference(self)

        # Set new reference
        value.addListReference(self)
        self.assignedObjects[index] = value

        # Set each attribute
        index = int(index)
        for attrName, attrType in self.attributes.items():

            objValue = getattr(value, attrName)

            # Cast values to correct types
            if attrType == "float":
                objValue = float(objValue)
            elif attrType == "int":
                objValue = int(objValue)
            if attrType == "array<int>(6)":
                for i in xrange(6):
                    self.ptaWrappers[attrName][index][i] = objValue[i]
            elif attrType == "mat4":
                self.ptaWrappers[attrName][index][0] = objValue
            else:
                self.ptaWrappers[attrName][index][0] = objValue
