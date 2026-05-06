"""
Pydantic Models
===============
Request/response schemas for the API.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class UserProfile(BaseModel):
    """User profile for evaluation"""
    bodyType: Optional[str] = None
    skinTone: Optional[str] = None
    undertone: Optional[str] = None
    height: Optional[str] = None
    bodyConcern: Optional[str] = None
    occasion: Optional[str] = None
    season: Optional[str] = None
    gender: Optional[str] = None
    ageBracket: Optional[str] = None
    budgetTier: Optional[str] = None
    stylePref: Optional[str] = None
    category: Optional[str] = None
    lifestyle: Optional[str] = None
    cultureRegion: Optional[str] = None
    hairColor: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "bodyType": "oval",
                "skinTone": "dark",
                "occasion": "wedding",
                "stylePref": "romantic",
            }
        }


class ActionScore(BaseModel):
    attr: str
    value: str
    score: float
    key: str
    sources: List[str] = []


class EvaluationResult(BaseModel):
    """Result of evaluating a user profile against rules"""
    recommend: List[ActionScore]
    avoid: List[ActionScore]
    all_scores: Dict[str, float]
    matched_rules: int
    matched_rule_names: List[str]


class Clause(BaseModel):
    field: str
    op: str = "IN"
    values: List[str]


class Conditions(BaseModel):
    operator: str = "AND"
    clauses: List[Clause]


class Action(BaseModel):
    attr: str
    value: str
    score: float


class RuleCreate(BaseModel):
    """Schema for creating/updating a rule"""
    id: Optional[str] = None
    name: Optional[str] = None
    isActive: bool = True
    priority: int = 5
    conditions: Conditions
    actions: List[Action]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "B01",
                "name": "Pear body",
                "isActive": True,
                "priority": 5,
                "conditions": {
                    "operator": "AND",
                    "clauses": [{"field": "bodyType", "op": "IN", "values": ["pear"]}]
                },
                "actions": [
                    {"attr": "fit", "value": "a_line", "score": 2.0},
                    {"attr": "fit", "value": "bodycon", "score": -2.5},
                ]
            }
        }
