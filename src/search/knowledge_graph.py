"""
Knowledge Graph Builder for relationship extraction and graph construction
"""
import re
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import json
import logging
from ..core.database import DatabaseManager
from ..core.config import config

# Optional imports for advanced NLP
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class Entity:
    """Represents an entity in the knowledge graph"""
    def __init__(self, name: str, entity_type: str, mentions: int = 1):
        self.name = name
        self.entity_type = entity_type
        self.mentions = mentions
        self.related_entities = set()
        self.documents = set()
    
    def to_dict(self):
        return {
            'name': self.name,
            'type': self.entity_type,
            'mentions': self.mentions,
            'related_entities': list(self.related_entities),
            'documents': list(self.documents)
        }


class Relationship:
    """Represents a relationship between entities"""
    def __init__(self, entity1: str, entity2: str, relation_type: str, confidence: float = 0.5):
        self.entity1 = entity1
        self.entity2 = entity2
        self.relation_type = relation_type
        self.confidence = confidence
        self.documents = set()
    
    def to_dict(self):
        return {
            'entity1': self.entity1,
            'entity2': self.entity2,
            'relation_type': self.relation_type,
            'confidence': self.confidence,
            'documents': list(self.documents)
        }


class KnowledgeGraphBuilder:
    """Build and manage knowledge graph from document content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        self.entities = {}  # name -> Entity
        self.relationships = []  # List of Relationship objects
        self.nlp_model = None
        self._initialize_nlp()
        self._initialize_database()
    
    def _initialize_nlp(self):
        """Initialize NLP models for entity extraction"""
        try:
            if SPACY_AVAILABLE:
                try:
                    self.nlp_model = spacy.load("en_core_web_sm")
                    self.logger.info("Loaded spaCy model for entity extraction")
                except OSError:
                    self.logger.warning("spaCy model not found. Using fallback methods.")
                    self.nlp_model = None
            else:
                self.logger.warning("spaCy not available. Using rule-based entity extraction.")
        except Exception as e:
            self.logger.error(f"Failed to initialize NLP model: {e}")
    
    def _initialize_database(self):
        """Initialize knowledge graph tables"""
        try:
            # Create entities table
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS kg_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    entity_type TEXT NOT NULL,
                    mentions INTEGER DEFAULT 1,
                    metadata JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create relationships table
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS kg_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity1_id INTEGER NOT NULL,
                    entity2_id INTEGER NOT NULL,
                    relation_type TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    source_documents JSON DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entity1_id) REFERENCES kg_entities(id),
                    FOREIGN KEY (entity2_id) REFERENCES kg_entities(id)
                )
            """)
            
            # Create document-entity associations
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS kg_document_entities (
                    document_id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    mentions INTEGER DEFAULT 1,
                    contexts JSON DEFAULT '[]',
                    PRIMARY KEY (document_id, entity_id),
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (entity_id) REFERENCES kg_entities(id)
                )
            """)
            
            # Create indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_kg_entities_type ON kg_entities(entity_type)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_kg_relationships_entities ON kg_relationships(entity1_id, entity2_id)")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge graph database: {e}")
    
    def extract_entities_from_document(self, document_id: int, title: str, content: str) -> Dict:
        """Extract entities from a document and update knowledge graph"""
        try:
            entities_found = {}
            
            # Combine title and content for entity extraction
            full_text = f"{title}\n\n{content}"
            
            if self.nlp_model:
                entities_found = self._extract_entities_spacy(full_text)
            else:
                entities_found = self._extract_entities_rule_based(full_text)
            
            # Store entities and relationships
            for entity_name, entity_data in entities_found.items():
                entity_id = self._store_entity(entity_name, entity_data['type'])
                self._associate_document_entity(document_id, entity_id, entity_data['mentions'], entity_data['contexts'])
            
            # Extract relationships between entities
            relationships = self._extract_relationships(full_text, list(entities_found.keys()))
            for rel in relationships:
                self._store_relationship(rel, document_id)
            
            self.logger.info(f"Extracted {len(entities_found)} entities and {len(relationships)} relationships from document {document_id}")
            
            return {
                'entities': len(entities_found),
                'relationships': len(relationships),
                'entity_types': list(set([e['type'] for e in entities_found.values()]))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract entities from document {document_id}: {e}")
            return {'entities': 0, 'relationships': 0, 'entity_types': []}
    
    def _extract_entities_spacy(self, text: str) -> Dict:
        """Extract entities using spaCy NLP model"""
        entities = {}
        doc = self.nlp_model(text)
        
        for ent in doc.ents:
            if len(ent.text.strip()) > 2:  # Filter out very short entities
                entity_name = ent.text.strip()
                entity_type = ent.label_
                
                if entity_name not in entities:
                    entities[entity_name] = {
                        'type': entity_type,
                        'mentions': 0,
                        'contexts': []
                    }
                
                entities[entity_name]['mentions'] += 1
                
                # Extract context around entity
                start = max(0, ent.start - 5)
                end = min(len(doc), ent.end + 5)
                context = ' '.join([token.text for token in doc[start:end]])
                entities[entity_name]['contexts'].append(context)
        
        return entities
    
    def _extract_entities_rule_based(self, text: str) -> Dict:
        """Extract entities using rule-based methods"""
        entities = {}
        
        # Simple patterns for common entity types
        patterns = {
            'PERSON': [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
                r'\b(?:Dr|Mr|Ms|Mrs|Prof)\. [A-Z][a-z]+\b'  # Title Name
            ],
            'ORG': [
                r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Organization)\b',
                r'\b(?:Google|Microsoft|Apple|Amazon|Facebook|IBM|Intel)\b'
            ],
            'TECH': [
                r'\b(?:Python|JavaScript|React|Django|Flask|SQL|HTML|CSS|API|ML|AI)\b',
                r'\b(?:machine learning|artificial intelligence|deep learning|neural network)\b'
            ],
            'DATE': [
                r'\b\d{4}\b',  # Years
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            ]
        }
        
        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group().strip()
                    if len(entity_name) > 2:
                        if entity_name not in entities:
                            entities[entity_name] = {
                                'type': entity_type,
                                'mentions': 0,
                                'contexts': []
                            }
                        
                        entities[entity_name]['mentions'] += 1
                        
                        # Extract context
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end].replace('\n', ' ')
                        entities[entity_name]['contexts'].append(context)
        
        return entities
    
    def _extract_relationships(self, text: str, entities: List[str]) -> List[Relationship]:
        """Extract relationships between entities"""
        relationships = []
        
        # Simple co-occurrence based relationships
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_entities = [e for e in entities if e.lower() in sentence.lower()]
            
            # Create relationships for entities appearing in the same sentence
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    relation_type = self._infer_relation_type(sentence, entity1, entity2)
                    confidence = 0.7 if relation_type != 'related_to' else 0.5
                    
                    relationships.append(Relationship(entity1, entity2, relation_type, confidence))
        
        return relationships
    
    def _infer_relation_type(self, sentence: str, entity1: str, entity2: str) -> str:
        """Infer relationship type from sentence context"""
        sentence_lower = sentence.lower()
        
        # Simple rule-based relationship inference
        if any(word in sentence_lower for word in ['created', 'developed', 'built', 'founded']):
            return 'created_by'
        elif any(word in sentence_lower for word in ['works', 'employed', 'at']):
            return 'works_at'
        elif any(word in sentence_lower for word in ['part of', 'belongs to', 'owned by']):
            return 'part_of'
        elif any(word in sentence_lower for word in ['similar', 'like', 'compared']):
            return 'similar_to'
        else:
            return 'related_to'
    
    def _store_entity(self, name: str, entity_type: str) -> int:
        """Store entity in database and return ID"""
        try:
            # Try to get existing entity
            existing = self.db.execute_query(
                "SELECT id, mentions FROM kg_entities WHERE name = ?", (name,)
            )
            
            if existing:
                # Update mention count
                entity_id = existing[0]['id']
                new_mentions = existing[0]['mentions'] + 1
                self.db.execute_update(
                    "UPDATE kg_entities SET mentions = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_mentions, entity_id)
                )
                return entity_id
            else:
                # Create new entity
                return self.db.execute_update(
                    "INSERT INTO kg_entities (name, entity_type) VALUES (?, ?)",
                    (name, entity_type), return_id=True
                )
        except Exception as e:
            self.logger.error(f"Failed to store entity {name}: {e}")
            return None
    
    def _associate_document_entity(self, document_id: int, entity_id: int, mentions: int, contexts: List[str]):
        """Associate document with entity"""
        try:
            self.db.execute_update("""
                INSERT OR REPLACE INTO kg_document_entities 
                (document_id, entity_id, mentions, contexts)
                VALUES (?, ?, ?, ?)
            """, (document_id, entity_id, mentions, json.dumps(contexts)))
        except Exception as e:
            self.logger.error(f"Failed to associate document {document_id} with entity {entity_id}: {e}")
    
    def _store_relationship(self, relationship: Relationship, document_id: int):
        """Store relationship in database"""
        try:
            # Get entity IDs
            entity1_id = self.db.execute_query(
                "SELECT id FROM kg_entities WHERE name = ?", (relationship.entity1,)
            )
            entity2_id = self.db.execute_query(
                "SELECT id FROM kg_entities WHERE name = ?", (relationship.entity2,)
            )
            
            if not entity1_id or not entity2_id:
                return
            
            entity1_id = entity1_id[0]['id']
            entity2_id = entity2_id[0]['id']
            
            # Check if relationship already exists
            existing = self.db.execute_query("""
                SELECT id, source_documents FROM kg_relationships 
                WHERE entity1_id = ? AND entity2_id = ? AND relation_type = ?
            """, (entity1_id, entity2_id, relationship.relation_type))
            
            if existing:
                # Update existing relationship
                rel_id = existing[0]['id']
                source_docs = json.loads(existing[0]['source_documents'])
                if document_id not in source_docs:
                    source_docs.append(document_id)
                    self.db.execute_update(
                        "UPDATE kg_relationships SET source_documents = ? WHERE id = ?",
                        (json.dumps(source_docs), rel_id)
                    )
            else:
                # Create new relationship
                self.db.execute_update("""
                    INSERT INTO kg_relationships 
                    (entity1_id, entity2_id, relation_type, confidence, source_documents)
                    VALUES (?, ?, ?, ?, ?)
                """, (entity1_id, entity2_id, relationship.relation_type, 
                     relationship.confidence, json.dumps([document_id])))
                
        except Exception as e:
            self.logger.error(f"Failed to store relationship: {e}")
    
    def get_entity_graph(self, entity_name: str, max_depth: int = 2) -> Dict:
        """Get entity and its relationships up to max_depth"""
        try:
            # Get entity info
            entity_data = self.db.execute_query(
                "SELECT * FROM kg_entities WHERE name = ?", (entity_name,)
            )
            
            if not entity_data:
                return {}
            
            entity = entity_data[0]
            graph = {
                'center_entity': entity,
                'related_entities': [],
                'relationships': []
            }
            
            # Get direct relationships
            relationships = self.db.execute_query("""
                SELECT r.*, e1.name as entity1_name, e2.name as entity2_name
                FROM kg_relationships r
                JOIN kg_entities e1 ON r.entity1_id = e1.id
                JOIN kg_entities e2 ON r.entity2_id = e2.id
                WHERE e1.name = ? OR e2.name = ?
            """, (entity_name, entity_name))
            
            related_entity_names = set()
            for rel in relationships:
                graph['relationships'].append(rel)
                if rel['entity1_name'] != entity_name:
                    related_entity_names.add(rel['entity1_name'])
                if rel['entity2_name'] != entity_name:
                    related_entity_names.add(rel['entity2_name'])
            
            # Get related entity details
            for name in related_entity_names:
                entity_info = self.db.execute_query(
                    "SELECT * FROM kg_entities WHERE name = ?", (name,)
                )
                if entity_info:
                    graph['related_entities'].append(entity_info[0])
            
            return graph
            
        except Exception as e:
            self.logger.error(f"Failed to get entity graph for {entity_name}: {e}")
            return {}
    
    def build_knowledge_graph_for_all_documents(self):
        """Build knowledge graph for all documents"""
        documents = self.db.execute_query("""
            SELECT id, title, content FROM documents WHERE status = 'active'
        """)
        
        processed = 0
        for doc in documents:
            result = self.extract_entities_from_document(doc['id'], doc['title'], doc['content'])
            if result['entities'] > 0:
                processed += 1
        
        self.logger.info(f"Built knowledge graph for {processed}/{len(documents)} documents")
        return processed
