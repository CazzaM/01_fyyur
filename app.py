#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Shows(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime())
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))

    def __repr(self):
        return f'<Show ID: {self.id}, start time: {self.start_time}, Artist ID: {self.artist_id}, Venue ID: {self.venue_id}>'

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False, default="No Facebook page")
    website = db.Column(db.String(120), nullable=False, default="No Website")
    genres = db.Column(db.ARRAY(db.String),nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(250), nullable=False, default="Not currently seeking talent")
    show_info = db.relationship('Shows', cascade="all, delete-orphan", backref='venues', primaryjoin=id ==Shows.venue_id)

    def __repr(self):
        return f'<Venue ID: {self.id}, name: {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable = False)
    image_link = db.Column(db.String(500), nullable=False)
    genres = db.Column(db.ARRAY(db.String),nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False, default="No Facebook page")
    website = db.Column(db.String(120), nullable=False, default="No Website")
    seeking_venues = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(250), nullable=False, default="Not currently seeking performance venues")
    show_info = db.relationship('Shows', cascade="all, delete-orphan", backref='artists', primaryjoin=id ==Shows.artist_id)

    def __repr(self):
        return f'<Artist ID: {self.id}, name: {self.name}>'


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#delete later
def display_exception(exc, msg, trace_on=True):
    """
    display_exception(Exception, string, bool) --> null

    Input exception and message, display message and exception info.
    """
    exc_type, exc_obj, exc_tb = exc_info()
    file_name = split(exc_tb.tb_frame.f_code.co_filename)[1]
    log_msg = "Message: {}; Type: {}; ".format(msg, exc_type.__name__) +\
                 "Args: {}; File: {}; ".format(str(exc_obj), file_name) +\
                 "Line: {}".format(str(exc_tb.tb_lineno))
    if trace_on:
        log_msg += 2*linesep + format_exc()
    print("ERROR: " + log_msg)

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
    error = False
    try:
        areas = Venue.query.with_entities(Venue.city, Venue.state).distinct()
        data = []
        entry = []
        for area in areas:
            count = 0
            show_data = []
            venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city)
            for venue in venues:
                shows = Shows.query.filter_by(venue_id=venue.id).all()
                for show in shows:
                    if show.start_time > datetime.now():
                      count += 1
                show_data.append({
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': count
                })
            entry.append({
                'city': area.city,
                'state': area.state,
                'venues' : show_data
            })
        data.append(entry)
    except Exception as e:
        print('Error building venues: ',e)
        for area in areas:
            print(area)
        error = True
    finally:
        if error:
            abort(500)
        else:
            print(data)
            return render_template('pages/venues.html',areas=data[0])
#  data=[{
#    "city": "San Francisco",
#    "state": "CA",
#    "venues": [{
#      "id": 1,
#      "name": "The Musical Hop",
#      "num_upcoming_shows": 0,
#    }, {
#      "id": 3,
#      "name": "Park Square Live Music & Coffee",
#      "num_upcoming_shows": 1,
#    }]
#  }, {
#    "city": "New York",
#    "state": "NY",
#    "venues": [{
#      "id": 2,
#      "name": "The Dueling Pianos Bar",
#      "num_upcoming_shows": 0,
#    }]
#  }]
#  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    error = False
    try:
        venue = Venue.query.get(venue_id)
        data = []
        upcomingShows = 0
        pastShows = 0
        upcoming_shows = []
        past_shows = []
        shows = Shows.query.filter_by(venue_id=venue.id).all()
        for show in shows:
            if show.start_time > datetime.now():
                print('got into the if start time > datetime.now')
                upcomingShows += 1
                print('before artist_info get')
                artist_info = Artist.query.get(id=venue.show_info.artist_id)
                print('after artist_info get')
                upcoming_shows.append({
                    'artist_id' : artist_info.id,
                    'artist_name' : artist_info.name,
                    'artist_image_link' : artist_info.image_link,
                    'start_time' : show.start_time
                })
            else:
                print('got into the if start time NOT > datetime.now')
                pastShows += 1
                print(pastShows)
                print(show.artist_id)
                artist_info = Artist.query.get(show.artist_id)
                print('got first artist_info')
                past_shows.append({
                    'artist_id' : artist_info.id,
                    'artist_name' : artist_info.name,
                    'artist_image_link' : artist_info.image_link,
                    'start_time' : show.start_time
                })
        data.append({
            'id': venue.id,
            'name': venue.name,
            'city': venue.city,
            'state': venue.state,
            'phone': venue.phone,
            'genres' : venue.genres,
            'address' : venue.address,
            'website' : venue.website,
            'facebook_link': venue.facebook_link,
            'seeking_talent': venue.seeking_talent,
            'seeking_description':venue.seeking_description,
            'image_link':venue.image_link,
            'past_shows_count': pastShows,
            'upcoming_shows_count': upcomingShows,
            'past_shows': past_shows,
            'upcoming_shows': upcoming_shows
        })
    except Exception as e:
        #display_exception(exc, "I want to know what happened here...")
        print('Error retrieving venue: ',e)
        print(data)
        error = True
    finally:
        if error:
           abort(500)
        else:
            print(data)
        return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
 form = VenueForm(request.form, meta={'csrf':False})
 if form.validate():
     try:
         venue = Venue()
         form.populate_obj(venue)
         db.session.add(venue)
         db.session.commit()
         # on successful db insert, flash success
         flash('Venue ' + request.form['name'] + ' was successfully listed!')
     except ValueError as e:
         print(e)
         # TODO: on unsuccessful db insert, flash an error instead.
         # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
         # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
         flash('Unable to list Venue ' + request.form['name'] + '!')
         db.session.rollback()
     finally:
         db.session.close()
 else:
     message = []
     for field, err in form.errors.items():
         message.append(field + ' ' + '|'.join(err))
     flash('Errors '+ str(message))

 return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
    return render_template('pages/artists.html',
    artists = Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

    error = False
    try:
        data = Artist.query.get(artist_id)
    except Exception as e:
        print('Error retrieving artist: ',e)
        for i in data:
            print(i)
        error = True
    finally:
        if error:
            abort(500)
        else:
            print(data)
            return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form, meta={'csrf':False})
  if form.validate():
      try:
          artist = Artist()
          form.populate_obj(artist)
          db.session.add(artist)
          db.session.commit()
          # on successful db insert, flash success
          flash('Artist ' + request.form['name'] + ' was successfully listed!')
      except ValueError as e:
          print(e)
          # TODO: on unsuccessful db insert, flash an error instead.
          # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
          flash('Unable to list Artist ' + request.form['name'] + '!')
          db.session.rollback()
      finally:
          db.session.close()
  else:
      message = []
      for field, err in form.errors.items():
          message.append(field + ' ' + '|'.join(err))
      flash('Errors '+ str(message))

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
    error = False
    try:
        shows = Shows.query.all()
        data = []
        for show in shows:
            venues = Venue.query.get(show.venue_id)
            artist = Artist.query.get(show.artist_id)
            data.append({
                'show_id': show.id,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M"),
                'artist_id' : show.artist_id,
                'artist_name' : artist.name,
                'artist_image_link' : artist.image_link,
                'venue_id' : show.venue_id,
                'venue_name' : venues.name
            })
    except Exception as e:
        print('Error building shows: ',e)
        print(data)
        error = True
    finally:
        if error:
            abort(500)
        else:
            print(data)
            return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
 form = ShowForm(request.form, meta={'csrf':False})
 if form.validate():
     try:
         show = Shows()
         form.populate_obj(show)
         db.session.add(show)
         db.session.commit()
         # on successful db insert, flash success
         flash('Show was successfully listed!')
     except ValueError as e:
         print(e)
          # TODO: on unsuccessful db insert, flash an error instead.
          # e.g., flash('An error occurred. Show could not be listed.')
          # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
         flash('Unable to list Show for date' + request.form['show_date'] + '!')
         db.session.rollback()
     finally:
         db.session.close()
 else:
     message = []
     for field, err in form.errors.items():
         message.append(field + ' ' + '|'.join(err))
     flash('Errors '+ str(message))

 return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
