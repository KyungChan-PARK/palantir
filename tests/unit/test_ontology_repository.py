import sys
import types
import uuid

sys.modules.setdefault('chromadb', types.ModuleType('chromadb'))
sys.modules.setdefault('chromadb.utils', types.ModuleType('chromadb.utils'))
class DummyClient:
    def create_collection(self, name=None, embedding_function=None):
        class DummyCollection:
            def add(self, *a, **k):
                pass

            def query(self, *a, **k):
                return {}

        return DummyCollection()

sys.modules['chromadb'].PersistentClient = lambda path: DummyClient()
class DummyEF:
    def __init__(self, model_name=None):
        pass
sys.modules['chromadb.utils'].embedding_functions = types.SimpleNamespace(
    SentenceTransformerEmbeddingFunction=DummyEF
)

from palantir.ontology.repository import OntologyRepository
from palantir.ontology.base import OntologyObject, OntologyLink


def test_ontology_crud_cycle():
    repo = OntologyRepository()
    obj = OntologyObject(id=uuid.uuid4(), type='Customer', properties={'name': 'A'})
    repo.add_object(obj)

    fetched = repo.get_object(obj.id, OntologyObject)
    assert fetched is not None
    assert fetched.properties['name'] == 'A'

    obj.properties['name'] = 'B'
    repo.update_object(obj)
    updated = repo.get_object(obj.id, OntologyObject)
    assert updated.properties['name'] == 'B'

    link = OntologyLink(source_id=obj.id, target_id=obj.id, relationship_type='SELF')
    repo.add_link(link)
    links = repo.get_linked_objects(obj.id)
    assert links and links[0]['relationship']['type'] == 'SELF'

    repo.delete_object(obj.id)
    assert repo.get_object(obj.id, OntologyObject) is None
