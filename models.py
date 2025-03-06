from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import timedelta
from database import db


class Event(db.Model):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # duration in minutes
    is_recurring = Column(Boolean, default=False)
    recurrence_days = Column(JSON, nullable=True)  # List of days [0-6]

    @classmethod
    def check_event_conflict(cls, new_event, exclude_id=None):
        """
        Check for scheduling conflicts, with proper time overlap detection

        Args:
            new_event: The event to check
            exclude_id: Optional ID to exclude from conflict check (for updates)

        Returns:
            bool: True if no conflict, False otherwise
        """
        # Calculate the end time for the new event
        new_event_end = new_event.start_datetime + \
            timedelta(minutes=new_event.duration)

        # Get all events except the one being updated
        if exclude_id is not None:
            existing_events = cls.query.filter(cls.id != exclude_id).all()
        else:
            existing_events = cls.query.all()

        for event in existing_events:
            # Calculate the end time for the existing event
            event_end = event.start_datetime + \
                timedelta(minutes=event.duration)

            # Case 1: Both events are recurring
            if new_event.is_recurring and event.is_recurring:
                # Check if there are any overlapping days
                new_days = set(new_event.recurrence_days or [])
                existing_days = set(event.recurrence_days or [])

                if not new_days or not existing_days:
                    continue

                overlapping_days = new_days & existing_days

                if overlapping_days:
                    # Check time overlaps
                    new_start_time = new_event.start_datetime.time()
                    new_end_time = new_event_end.time()

                    event_start_time = event.start_datetime.time()
                    event_end_time = event_end.time()

                    # Check for time overlap
                    if cls._times_overlap(new_start_time, new_end_time, event_start_time, event_end_time):
                        return False

            # Case 2: Both events are non-recurring
            elif not new_event.is_recurring and not event.is_recurring:
                # For non-recurring events, check date and time overlap
                if (new_event.start_datetime <= event_end and
                        new_event_end >= event.start_datetime):
                    return False

            # Case 3: New event is recurring, existing event is non-recurring
            elif new_event.is_recurring and not event.is_recurring:
                # Check if the day of the week of the non-recurring event
                # is in the recurrence days of the recurring event
                event_day_of_week = event.start_datetime.weekday()

                # Python's weekday() returns 0-6 (Monday is 0)
                # If using a different convention, we need to convert
                if event_day_of_week in (new_event.recurrence_days or []):
                    # Check time overlap
                    new_start_time = new_event.start_datetime.time()
                    new_end_time = new_event_end.time()

                    event_start_time = event.start_datetime.time()
                    event_end_time = event_end.time()

                    if cls._times_overlap(new_start_time, new_end_time, event_start_time, event_end_time):
                        return False

            # Case 4: New event is non-recurring, existing event is recurring
            elif not new_event.is_recurring and event.is_recurring:
                # Check if the day of the week of the non-recurring event
                # is in the recurrence days of the recurring event
                new_event_day_of_week = new_event.start_datetime.weekday()

                if new_event_day_of_week in (event.recurrence_days or []):
                    # Check time overlap
                    new_start_time = new_event.start_datetime.time()
                    new_end_time = new_event_end.time()

                    event_start_time = event.start_datetime.time()
                    event_end_time = event_end.time()

                    if cls._times_overlap(new_start_time, new_end_time, event_start_time, event_end_time):
                        return False

        return True

    @staticmethod
    def _times_overlap(start_a, end_a, start_b, end_b):
        """
        Check if two time ranges overlap

        Args:
            start_a, end_a: Start and end times for first event
            start_b, end_b: Start and end times for second event

        Returns:
            bool: True if times overlap, False otherwise
        """
        # Check for time overlap
        return (start_a <= end_b) and (end_a >= start_b)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_datetime': self.start_datetime.isoformat(),
            'duration': self.duration,
            'is_recurring': self.is_recurring,
            'recurrence_days': self.recurrence_days
        }
