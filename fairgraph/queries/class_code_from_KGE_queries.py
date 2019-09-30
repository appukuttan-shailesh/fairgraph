import sys
from build_KG_queries import *

# THe classes below were manually copy-pasted from the KG-Editor interface
MINDS_CLASSES = [
    {'Activity':'core/activity/v1.0.0'},
    {'Agecategory':'core/agecategory/v1.0.0'},
    {'Approval':'ethics/approval/v1.0.0'},
    {'Authority':'ethics/authority/v1.0.0'},
    {'Dataset':'core/dataset/v1.0.0'},
    {'Embargostatus':'core/embargostatus/v1.0.0'},
    {'File':'core/file/v0.0.4'},
    {'Fileassociation':'core/fileassociation/v1.0.0'},
    # {'Fileassociation':'core/fileassociation/v0.0.4'},
    {'Format':'core/format/v1.0.0'},
    {'Licensetype':'core/licensetype/v1.0.0'},
    # {'Method':'experiment/method/v1.0.0'},
    {'Method':'core/method/v1.0.0'},
    {'Modality':'core/modality/v1.0.0'},
    {'Parcellationatlas':'core/parcellationatlas/v1.0.0'},
    {'Parcellationregion':'core/parcellationregion/v1.0.0'},
    {'Person':'core/person/v1.0.0'},
    {'Placomponent':'core/placomponent/v1.0.0'},
    {'Preparation':'core/preparation/v1.0.0'},
    {'Protocol':'experiment/protocol/v1.0.0'},
    {'Publication':'core/publication/v1.0.0'},
    {'Referencespace':'core/referencespace/v1.0.0'},
    # {'Release':'prov/release/v0.0.1'},
    {'Role':'prov/role/v1.0.0'},
    {'Sample':'experiment/sample/v1.0.0'},
    {'Sex':'core/sex/v1.0.0'},
    {'Softwareagent':'core/softwareagent/v1.0.0'},
    {'Species':'core/species/v1.0.0'},
    {'Specimengroup':'core/specimengroup/v1.0.0'},
    {'Subject':'experiment/subject/v1.0.0'}]

UNIMINDS_CLASSES = [
    {'Abstractionlevel':'options/abstractionlevel/v1.0.0'},
    {'Agecategory':'options/agecategory/v1.0.0'},
    {'Brainstructure':'options/brainstructure/v1.0.0'},
    {'Cellulartarget':'options/cellulartarget/v1.0.0'},
    {'Country':'options/country/v1.0.0'},
    {'Dataset':'core/dataset/v1.0.0'},
    {'Disability':'options/disability/v1.0.0'},
    {'Doi':'options/doi/v1.0.0'},
    {'Embargostatus':'options/embargostatus/v1.0.0'},
    {'Ethicsapproval':'core/ethicsapproval/v1.0.0'},
    {'Ethicsauthority':'options/ethicsauthority/v1.0.0'},
    {'Experimentalpreparation':'options/experimentalpreparation/v1.0.0'},
    {'File':'core/file/v1.0.0'},
    {'Fileassociation':'core/fileassociation/v1.0.0'},
    {'Filebundle':'core/filebundle/v1.0.0'},
    {'Filebundlegroup':'options/filebundlegroup/v1.0.0'},
    {'Fundinginformation':'core/fundinginformation/v1.0.0'},
    {'Genotype':'options/genotype/v1.0.0'},
    {'Handedness':'options/handedness/v1.0.0'},
    {'Hbpcomponent':'core/hbpcomponent/v1.0.0'},
    {'License':'options/license/v1.0.0'},
    {'Method':'core/method/v1.0.0'},
    {'Methodcategory':'options/methodcategory/v1.0.0'},
    {'Mimetype':'options/mimetype/v1.0.0'},
    {'Modelformat':'options/modelformat/v1.0.0'},
    {'Modelinstance':'core/modelinstance/v1.0.0'},
    {'Modelscope':'options/modelscope/v1.0.0'},
    {'Organization':'options/organization/v1.0.0'},
    {'Person':'core/person/v1.0.0'},
    {'Project':'core/project/v1.0.0'},
    {'Publication':'core/publication/v1.0.0'},
    {'Publicationid':'options/publicationid/v1.0.0'},
    {'Publicationidtype':'options/publicationidtype/v1.0.0'},
    {'Sex':'options/sex/v1.0.0'},
    {'Species':'options/species/v1.0.0'},
    {'Strain':'options/strain/v1.0.0'},
    {'Studytarget':'core/studytarget/v1.0.0'},
    {'Studytargetsource':'options/studytargetsource/v1.0.0'},
    {'Studytargettype':'options/studytargettype/v1.0.0'},
    {'Subject':'core/subject/v1.0.0'},
    {'Subjectgroup':'core/subjectgroup/v1.0.0'},
    {'Tissuesample':'core/tissuesample/v1.0.0'}]


def typename_dict(field):
    # if field=='name':
    #     return 'basestring'
    # else:
    #     return 'str'
    return 'basestring'

def field_dict(field):
    if field=='@id':
        return 'id'
    elif field=='@type':
        return 'type'
    else:
        return field
    
def required_dict(field):
    if field in ['name', 'identifier', '@id', 'id']:
        return 'True'
    else:
        return 'False'
    
def transform_KGE_query_to_dict(namespace, cls, cls_version):
    """
    Requirements:
    for all the NAMESPACES, you have generated a query using the builder in the Knowledge graph Editor
    https://kg.humanbrainproject.org/editor/query-builder

    For each namespace (e.g. "Dataset"), you have saved the query in the KGE with the "fg-KGE" suffix
    i.e. for the "Dataset" namespace, the query can be found at:
    https://kg.humanbrainproject.org/query/minds/core/dataset/v1.0.0/fg-KGE
    """

    r=requests.get(query_url(namespace, cls_version)+'-KGE',
          headers={'Content-Type':'application/json',
                   'Authorization': 'Bearer {}'.format(access_token)})
    new_query_dict = {}
    if r.ok:
        open('temp.json', 'wb').write(r.content)
        with open('temp.json', 'r') as f:
            KGE_dict = json.load(f)

        for key, value in KGE_dict.items():
            if type(value)==dict:
                # new_query_dict[key] = {}
                # for key2, value2 in value.items():
                #     if key2!='fieldname':
                #         new_query_dict[key][key2] = value2
                new_query_dict[key] = value # no need to delete the fieldname entry here
            elif type(value)==list:
                new_query_dict[key] = []
                for value2 in value:
                    new_query_dict[key].append({})
                    for key3, value3 in value2.items():
                        if key3!='fieldname':
                            new_query_dict[key][-1][key3] = value3
                        else:
                            new_query_dict[key][-1]['field'] = value3.split('query:')[1]
                            
            else:
                new_query_dict[key] = value
    else:
        print('Problem with url: %s' % query_url(namespace, cls_version)+'-KGE')
        
    return new_query_dict

def extract_fields_from_query(query_dict):
    FIELD = 'fields = (\\\n'
    for i, field in enumerate(query_dict['fields']):
        try:
            relative_path = field['relative_path']
        except KeyError:
            relative_path = ''
        if i>0:
            FIELD += ',\n'
        FIELD += '      Field("%s", %s, "%s", required=%s)' % (field_dict(field['field']),
                                                    typename_dict(field['field']),
                                                    relative_path,
                                                    required_dict(field['field']))
    FIELD += ')'
    return FIELD

def generate_code_for_class_def(nmspc, cls, cls_version, FIELD):
    return '''

class %s(MINDSObject):
    """
    docstring
    """
    _path = "/%s"
    type = ["%s:%s"]

    def __repr__(self):
        return ('{self.__class__.__name__}('
                '{self.name!r} {self.id!r})'.format(self=self))
    %s
    ''' % (cls, cls_version, nmspc.lower(), cls, FIELD)
    

if __name__=='__main__':
    if sys.argv[-1]=='Minds':
        for mc in MINDS_CLASSES:
            cls, cls_version = list(mc.keys())[0], list(mc.values())[0]
            query = transform_KGE_query_to_dict(sys.argv[-1], cls, cls_version)
            FIELDS = extract_fields_from_query(query)
            code = generate_code_for_class_def(sys.argv[-1], cls, cls_version, FIELDS)
            print(code)
    elif sys.argv[-1]=='Uniminds':
        for mc in UNIMINDS_CLASSES:
            cls, cls_version = list(mc.keys())[0], list(mc.values())[0]
            query = transform_KGE_query_to_dict(sys.argv[-1], cls, cls_version)
            FIELDS = extract_fields_from_query(query)
            code = generate_code_for_class_def(sys.argv[-1], cls, cls_version, FIELDS)
            print(code)
    else:
        print("""
        Please provide the namespace as an argument, either "Minds" of "Uniminds"
        e.g. run "python generate_fields_from_KGE_queries.py Minds"
        """)
