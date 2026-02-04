"""Tools package initialization."""
from .ticket_tools import (
    create_ticket,
    track_ticket,
    update_ticket,
    execute_create_ticket,
    execute_track_ticket,
    execute_update_ticket
)

from .booking_tools import (
    book_room,
    track_booking,
    update_booking,
    cancel_booking,
    execute_create_booking,
    execute_track_booking,
    execute_update_booking,
    execute_cancel_booking
)

from .rag_tools import (
    search_fpt_policies,
    search_fpt_policies_with_scores,
    get_vectorstore,
    preload_vectorstore
)

from .search_tools import (
    search_it_solutions,
    search_it_solutions_vietnamese
)

# Tool collections for agents
TICKET_TOOLS = [create_ticket, track_ticket, update_ticket]
BOOKING_TOOLS = [book_room, track_booking, update_booking, cancel_booking]
FAQ_TOOLS = [search_fpt_policies]
IT_SUPPORT_TOOLS = [search_it_solutions, search_it_solutions_vietnamese]

# Action executors mapping
ACTION_EXECUTORS = {
    "create_ticket": execute_create_ticket,
    "track_ticket": execute_track_ticket,
    "update_ticket": execute_update_ticket,
    "create_booking": execute_create_booking,
    "track_booking": execute_track_booking,
    "update_booking": execute_update_booking,
    "cancel_booking": execute_cancel_booking,
}

__all__ = [
    # Ticket tools
    "create_ticket",
    "track_ticket", 
    "update_ticket",
    "execute_create_ticket",
    "execute_track_ticket",
    "execute_update_ticket",
    
    # Booking tools
    "book_room",
    "track_booking",
    "update_booking",
    "cancel_booking",
    "execute_create_booking",
    "execute_track_booking",
    "execute_update_booking",
    "execute_cancel_booking",
    
    # RAG tools
    "search_fpt_policies",
    "search_fpt_policies_with_scores",
    "get_vectorstore",
    "preload_vectorstore",
    
    # Search tools
    "search_it_solutions",
    "search_it_solutions_vietnamese",
    
    # Tool collections
    "TICKET_TOOLS",
    "BOOKING_TOOLS",
    "FAQ_TOOLS",
    "IT_SUPPORT_TOOLS",
    "ACTION_EXECUTORS",
]
