from flask import Flask, request, jsonify, render_template
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from datetime import datetime
from database import db, init_db
from models import Event

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ma = Marshmallow(app)
init_db(app)


class EventSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Event
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    start_datetime = ma.DateTime(required=True)
    duration = ma.auto_field()
    is_recurring = ma.auto_field()
    recurrence_days = ma.List(ma.Integer())


event_schema = EventSchema()
events_schema = EventSchema(many=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/events', methods=['POST'])
def create_event():
    try:
        event_data = event_schema.load(request.json)

        if not Event.check_event_conflict(event_data):
            return jsonify({"error": "Event conflicts with existing events"}), 400

        db.session.add(event_data)
        db.session.commit()
        return event_schema.jsonify(event_data), 201
    except ValidationError as err:
        return jsonify(err.messages), 400


@app.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return events_schema.jsonify(events)


@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return event_schema.jsonify(event)


@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        event_data = request.json

        # Update fields
        event.name = event_data.get('name', event.name)

        # Handle start_datetime
        if 'start_datetime' in event_data:
            event.start_datetime = datetime.fromisoformat(
                event_data['start_datetime'])

        event.duration = event_data.get('duration', event.duration)
        event.is_recurring = event_data.get('is_recurring', event.is_recurring)

        # Handle recurrence_days
        if 'recurrence_days' in event_data:
            event.recurrence_days = event_data['recurrence_days']

        # Check for conflicts, excluding the current event
        if not Event.check_event_conflict(event, exclude_id=event_id):
            return jsonify({"error": "Event conflicts with existing events"}), 400

        db.session.commit()
        return event_schema.jsonify(event), 200
    except Exception as err:
        return jsonify({"error": str(err)}), 400


@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": f"Event {event_id} successfully deleted"}), 200


if __name__ == '__main__':
    app.run(debug=True)
