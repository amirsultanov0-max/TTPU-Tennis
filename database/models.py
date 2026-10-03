from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Base class for all database models.
    """

    pass


# ============================================================
# GROUP MODEL
# ============================================================


class Group(Base):

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    users: Mapped[list["User"]] = relationship(
        back_populates="group",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


# ============================================================
# USER MODEL
# ============================================================


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )

    telegram_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey(
            "groups.id",
            name="fk_users_group",
        ),
        nullable=False,
    )

    student_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    ranking_points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
    )

    wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --------------------------------------------------------
    # GROUP
    # --------------------------------------------------------

    group: Mapped["Group"] = relationship(
        back_populates="users",
    )

    # --------------------------------------------------------
    # MATCHES
    # --------------------------------------------------------

    matches_as_player_one: Mapped[list["Match"]] = relationship(
        foreign_keys="Match.player_one_id",
        back_populates="player_one",
    )

    matches_as_player_two: Mapped[list["Match"]] = relationship(
        foreign_keys="Match.player_two_id",
        back_populates="player_two",
    )

    matches_won: Mapped[list["Match"]] = relationship(
        foreign_keys="Match.winner_id",
        back_populates="winner",
    )

    matches_lost: Mapped[list["Match"]] = relationship(
        foreign_keys="Match.loser_id",
        back_populates="loser",
    )

    # --------------------------------------------------------
    # RESULT SUBMISSIONS
    # --------------------------------------------------------

    results_submitted: Mapped[list["Match"]] = relationship(
        foreign_keys="Match.result_submitted_by_id",
        back_populates="result_submitted_by",
    )

    # --------------------------------------------------------
    # CHALLENGES
    # --------------------------------------------------------

    sent_challenges: Mapped[list["Challenge"]] = relationship(
        foreign_keys="Challenge.challenger_id",
        back_populates="challenger",
    )

    received_challenges: Mapped[list["Challenge"]] = relationship(
        foreign_keys="Challenge.opponent_id",
        back_populates="opponent",
    )

    # --------------------------------------------------------
    # SCHEDULE REQUESTS
    # --------------------------------------------------------

    sent_schedule_requests: Mapped[
        list["ScheduleRequest"]
    ] = relationship(
        foreign_keys="ScheduleRequest.requested_by_id",
        back_populates="requested_by",
    )

    received_schedule_requests: Mapped[
        list["ScheduleRequest"]
    ] = relationship(
        foreign_keys="ScheduleRequest.recipient_id",
        back_populates="recipient",
    )

    def __repr__(self) -> str:
        return f"<User {self.first_name} {self.last_name}>"


# ============================================================
# MATCH MODEL
# ============================================================


class Match(Base):

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    player_one_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_match_player_one",
        ),
        nullable=False,
    )

    player_two_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_match_player_two",
        ),
        nullable=False,
    )

    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_match_winner",
        ),
        nullable=True,
    )

    loser_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_match_loser",
        ),
        nullable=True,
    )

    competition_type: Mapped[str] = mapped_column(
        String(20),
        default="friendly",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="awaiting_schedule",
        nullable=False,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    played_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # RESULT WORKFLOW
    # ========================================================

    result_status: Mapped[str] = mapped_column(
        String(30),
        default="not_submitted",
        nullable=False,
    )

    result_submitted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_match_result_submitted_by",
        ),
        nullable=True,
    )

    # --------------------------------------------------------
    # BEST-OF-3 SET SCORES
    # --------------------------------------------------------

    set_1_player_one_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    set_1_player_two_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    set_2_player_one_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    set_2_player_two_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    set_3_player_one_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    set_3_player_two_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    result_submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    result_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ========================================================
    # RESULT REMINDER
    # ========================================================

    result_reminder_sent_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ========================================================
    # PLAYERS
    # ========================================================

    player_one: Mapped["User"] = relationship(
        foreign_keys=[player_one_id],
        back_populates="matches_as_player_one",
    )

    player_two: Mapped["User"] = relationship(
        foreign_keys=[player_two_id],
        back_populates="matches_as_player_two",
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    winner: Mapped["User | None"] = relationship(
        foreign_keys=[winner_id],
        back_populates="matches_won",
    )

    loser: Mapped["User | None"] = relationship(
        foreign_keys=[loser_id],
        back_populates="matches_lost",
    )

    # ========================================================
    # RESULT SUBMISSION
    # ========================================================

    result_submitted_by: Mapped["User | None"] = relationship(
        foreign_keys=[result_submitted_by_id],
        back_populates="results_submitted",
    )

    # ========================================================
    # SCHEDULING
    # ========================================================

    schedule_requests: Mapped[
        list["ScheduleRequest"]
    ] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Match {self.player_one_id} "
            f"vs {self.player_two_id}>"
        )


# ============================================================
# CHALLENGE MODEL
# ============================================================


class Challenge(Base):
    """
    Challenge request between two tennis players.
    """

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    challenger_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_challenge_challenger",
        ),
        nullable=False,
    )

    opponent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_challenge_opponent",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ========================================================
    # PLAYERS
    # ========================================================

    challenger: Mapped["User"] = relationship(
        foreign_keys=[challenger_id],
        back_populates="sent_challenges",
    )

    opponent: Mapped["User"] = relationship(
        foreign_keys=[opponent_id],
        back_populates="received_challenges",
    )

    def __repr__(self) -> str:
        return (
            f"<Challenge "
            f"{self.challenger_id} -> {self.opponent_id} "
            f"({self.status})>"
        )


# ============================================================
# SCHEDULE REQUEST MODEL
# ============================================================


class ScheduleRequest(Base):
    """
    Request to schedule a match at a proposed date and time.

    The proposed time only becomes official after
    the recipient accepts the request.
    """

    __tablename__ = "schedule_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    match_id: Mapped[int] = mapped_column(
        ForeignKey(
            "matches.id",
            name="fk_schedule_request_match",
        ),
        nullable=False,
    )

    requested_by_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_schedule_request_requested_by",
        ),
        nullable=False,
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_schedule_request_recipient",
        ),
        nullable=False,
    )

    proposed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ========================================================
    # MATCH
    # ========================================================

    match: Mapped["Match"] = relationship(
        back_populates="schedule_requests",
    )

    # ========================================================
    # USERS
    # ========================================================

    requested_by: Mapped["User"] = relationship(
        foreign_keys=[requested_by_id],
        back_populates="sent_schedule_requests",
    )

    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id],
        back_populates="received_schedule_requests",
    )

    def __repr__(self) -> str:
        return (
            f"<ScheduleRequest "
            f"match={self.match_id} "
            f"status={self.status}>"
        )


# ============================================================
# INDEXES
# ============================================================


Index(
    "idx_user_ranking",
    User.ranking_points.desc(),
)

Index(
    "idx_match_status",
    Match.status,
)

Index(
    "idx_match_result_status",
    Match.result_status,
)

Index(
    "idx_match_result_submitted_by",
    Match.result_submitted_by_id,
)

Index(
    "idx_challenge_opponent_status",
    Challenge.opponent_id,
    Challenge.status,
)

Index(
    "idx_challenge_challenger_status",
    Challenge.challenger_id,
    Challenge.status,
)

Index(
    "idx_schedule_request_match_status",
    ScheduleRequest.match_id,
    ScheduleRequest.status,
)

Index(
    "idx_schedule_request_recipient_status",
    ScheduleRequest.recipient_id,
    ScheduleRequest.status,
)