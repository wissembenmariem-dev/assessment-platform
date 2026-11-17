from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID


class SessionCreate(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    level: str
    modules: List[str]
    lang: str = "fr"
    position_visee: Optional[str] = None
    entreprise_cible: Optional[str] = None


class SessionOut(BaseModel):
    id: UUID
    candidate_name: str
    candidate_email: str
    level: str
    modules: Any
    lang: str
    token: str
    status: str
    score_global: Optional[int] = None
    position_visee: Optional[str] = None
    entreprise_cible: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class SessionPublic(BaseModel):
    id: UUID
    candidate_name: str
    level: str
    modules: Any
    lang: str
    status: str


class ConsentStart(BaseModel):
    consent_given:   bool = False
    consent_version: str  = "v1.0"


class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    id: UUID
    module: int
    position: int
    type: str
    category: Optional[str]
    text: str
    instruction: Optional[str]
    options: List[QuestionOption]
    difficulty: int
    meta: Optional[Dict[str, Any]]


class AnswerSubmit(BaseModel):
    question_id: UUID
    module: int
    response: Dict[str, Any]


class BulkAnswerSubmit(BaseModel):
    answers: List[AnswerSubmit]


class M1Score(BaseModel):
    raw: int
    level: str
    by_section: Dict[str, int]


class M2Ocean(BaseModel):
    O: int
    C: int
    E: int
    A: int
    N: int
    archetype: str
    social_desirability: bool


class M3Score(BaseModel):
    raw: int
    level: str
    by_dim: Dict[str, int]
    style: str


class M4Score(BaseModel):
    engagement: int
    values: Dict[str, Any]


class Signal(BaseModel):
    type: str
    modules: List[str]
    label: str
    detail: str


class ReportText(BaseModel):
    m1_narrative: Optional[str] = None
    m2_narrative: Optional[str] = None
    m3_narrative: Optional[str] = None
    m4_narrative: Optional[str] = None
    global_narrative: str = ""
    interview_questions: List[str] = []
    ai_disclaimer: Optional[str] = None


class ScoreOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_id: UUID
    candidate_name: str
    level: str

    m1: M1Score
    m2: M2Ocean
    m3: Optional[M3Score]
    m4: M4Score

    global_score: int
    global_label: str

    signals: List[Signal]
    report: ReportText

    model_used: str
    computed_at: datetime


class RecruiterOut(BaseModel):
    id: UUID
    email: str
    name: str
    role: str


class DashboardStats(BaseModel):
    total_sent: int
    total_completed: int
    completion_rate: float
    avg_score: Optional[float]
    pending_count: int
