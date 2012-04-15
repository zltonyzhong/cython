# The hacks that are specific for NumPy. These were introduced because
# the NumPy ABI changed so that the shape, ndim, strides, etc. fields were
# no longer available, however the use of these were so entrenched in
# Cython codes
import os
from StringEncoding import EncodedString

def should_apply_numpy_hack(obj_type):
    if not obj_type.is_extension_type or obj_type.objstruct_cname != 'PyArrayObject':
        return False
    from Scanning import FileSourceDescriptor
    from Main import standard_include_path
    type_source = obj_type.pos[0]
    if isinstance(type_source, FileSourceDescriptor):
        type_source_path = os.path.abspath(os.path.normpath(type_source.filename))
        return type_source_path == os.path.join(standard_include_path, 'numpy.pxd')
    else:
        return False

def numpy_transform_attribute_node(node):
    import PyrexTypes
    import ExprNodes
    assert isinstance(node, ExprNodes.AttributeNode)

    if node.obj.type.objstruct_cname != 'PyArrayObject':
        return node

    pos = node.pos
    numpy_pxd_scope = node.obj.entry.type.scope.parent_scope
        
    def macro_call_node(numpy_macro_name):
        array_node = node.obj
        func_entry = numpy_pxd_scope.entries[numpy_macro_name]
        function_name_node = ExprNodes.NameNode(
            name=EncodedString(numpy_macro_name),
            pos=pos,
            entry=func_entry,
            is_called=1,
            type=func_entry.type,
            cf_maybe_null=False,
            cf_is_null=False)
        
        call_node = ExprNodes.SimpleCallNode(
            pos=pos,
            function=function_name_node,
            name=EncodedString(numpy_macro_name),
            args=[array_node],
            type=func_entry.type.return_type,
            analysed=True)
        return call_node
        
    
    if node.attribute == u'ndim':
        result = macro_call_node(u'PyArray_NDIM')
    elif node.attribute == u'data':
        call_node = macro_call_node(u'PyArray_DATA')
        cast_node = ExprNodes.TypecastNode(pos,
                                           type=PyrexTypes.c_char_ptr_type,
                                           operand=call_node)
        result = cast_node
    elif node.attribute == u'shape':
        result = macro_call_node(u'PyArray_DIMS')
    elif node.attribute == u'strides':
        result = macro_call_node(u'PyArray_STRIDES')
    else:
        result = node
    return result
