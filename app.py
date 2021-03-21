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
  # NO POINT IN UPDATING NUMBER OF SHOWS BECAUSE NOTHING IS DONE WITH IT IN THE VIEW
    error = False
    try:
        areas = Venue.query.with_entities(Venue.city, Venue.state).distinct()
        data = []
        entry = []
        for area in areas:
            venue_data = []
            venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city)
            for venue in venues:
                venue_data.append({
                    'id': venue.id,
                    'name': venue.name
                })
            entry.append({
                'city': area.city,
                'state': area.state,
                'venues' : venue_data
            })
        data = entry
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
            return render_template('pages/venues.html',areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # NO POINT IN COUNTING NUMBER OF UPCOMING SHOWS BECAUSE NOTHING IS DONE WITH IT IN THE VIEW
    error = False
    try:
        data = []
        search_term = request.form.get('search_term', '')
        venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
        count = len(venues)
        for venue in venues:
            data.append({
                'id': venue.id,
                'name': venue.name,
            })
        response = {
            'count': count,
            'data': data,
        }
    except Exception as e:
        print('Error retrieving search data: ',e)
        error = True
    finally:
        if error:
            abort(500)
        else:
            return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
    error = False
    try:
        venue = Venue.query.get(venue_id)
        data = ''
        upcomingShows = 0
        pastShows = 0
        upcoming_shows = []
        past_shows = []
        shows = Shows.query.filter_by(venue_id=venue.id).all()
        for show in shows:
            if show.start_time > datetime.now():
                upcomingShows += 1
                artist_info = Artist.query.get(show.artist_id)
                upcoming_shows.append({
                    'artist_id' : artist_info.id,
                    'artist_name' : artist_info.name,
                    'artist_image_link' : artist_info.image_link,
                    'start_time' : show.start_time.strftime("%m/%d/%Y, %H:%M")
                })
            else:
                pastShows += 1
                artist_info = Artist.query.get(show.artist_id)
                past_shows.append({
                    'artist_id' : artist_info.id,
                    'artist_name' : artist_info.name,
                    'artist_image_link' : artist_info.image_link,
                    'start_time' : show.start_time.strftime("%m/%d/%Y, %H:%M")
                })
        data = {
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
        }
    except Exception as e:
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

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except ValueError as e:
        flash('Unable to delete Venue ' + venue.name + '!')
        db.session.rollback()
    finally:
        db.session.close()

    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html',
    artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    # NO POINT IN COUNTING NUMBER OF UPCOMING SHOWS BECAUSE NOTHING IS DONE WITH IT IN THE VIEW
    error = False
    try:
        data = []
        search_term = request.form.get('search_term', '')
        artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
        count = len(artists)
        for artist in artists:
            data.append({
                'id': artist.id,
                'name': artist.name,
            })
        response = {
            'count': count,
            'data': data,
        }
    except Exception as e:
        print('Error retrieving search data: ',e)
        error = True
    finally:
        if error:
            abort(500)
        else:
            return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    error = False
    try:
        artist = Artist.query.get(artist_id)
        data = ''
        upcomingShows = 0
        pastShows = 0
        upcoming_shows = []
        past_shows = []
        shows = Shows.query.filter_by(artist_id=artist.id).all()
        for show in shows:
            venue_info = Venue.query.get(show.venue_id)
            if show.start_time > datetime.now():
                upcomingShows += 1
                upcoming_shows.append({
                    'venue_image_link' : venue_info.image_link,
                    'venue_id' : venue_info.id,
                    'venue_name' : venue_info.name,
                    'start_time' : show.start_time.strftime("%m/%d/%Y, %H:%M")
                })
            else:
                pastShows += 1
                past_shows.append({
                    'venue_image_link' : venue_info.image_link,
                    'venue_id' : venue_info.id,
                    'venue_name' : venue_info.name,
                    'start_time' : show.start_time.strftime("%m/%d/%Y, %H:%M")
                })
        data = {
            'id': artist.id,
            'name': artist.name,
            'city': artist.city,
            'state': artist.state,
            'phone': artist.phone,
            'genres' : artist.genres,
            'website' : artist.website,
            'facebook_link': artist.facebook_link,
            'seeking_venue': artist.seeking_venues,
            'seeking_description':artist.seeking_description,
            'image_link':artist.image_link,
            'past_shows_count': pastShows,
            'upcoming_shows_count': upcomingShows,
            'past_shows': past_shows,
            'upcoming_shows': upcoming_shows
        }
    except Exception as e:
        print('Error retrieving artist: ',e)
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
    print('just got into artist edit controller section')
    error = False
    try:
        artist = Artist.query.get(artist_id)
        form = ArtistForm(obj=artist)
    except Exception as e:
        print('Error populating artist form: ',e)
        error = True
    finally:
        if error:
            abort(500)
        else:
            print(form)
            return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # called upon submitting the new artist listing form
    form = ArtistForm(request.form, meta={'csrf':False})
    if form.validate():
      try:
          artist = Artist.query.get(artist_id)
          form.populate_obj(artist)
          db.session.commit()
          # on successful db insert, flash success
          flash('Artist ' + request.form['name'] + ' was successfully changed!')
      except ValueError as e:
          print(e)
          # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
          flash('Unable to edit Artist ' + request.form['name'] + '!')
          db.session.rollback()
      finally:
          db.session.close()
    else:
      message = []
      for field, err in form.errors.items():
          message.append(field + ' ' + '|'.join(err))
      flash('Errors '+ str(message))

    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/<artist_id>', methods=['POST'])
def delete_artist(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully deleted!')
    except ValueError as e:
        flash('Unable to delete Artist ' + artist.name + '!')
        db.session.rollback()
    finally:
        db.session.close()

    return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        form = VenueForm(obj=venue)
    except Exception as e:
        print('Error populating venue form: ',e)
        error = True
    finally:
        if error:
            abort(500)
        else:
            print(form)
            return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form, meta={'csrf':False})
    if form.validate():
      try:
          venue = Venue.query.get(venue_id)
          form.populate_obj(venue)
          db.session.commit()
          # on successful db insert, flash success
          flash('Venue ' + request.form['name'] + ' was successfully changed!')
      except ValueError as e:
          print(e)
          # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
          flash('Unable to edit Venue ' + request.form['name'] + '!')
          db.session.rollback()
      finally:
          db.session.close()
    else:
      message = []
      for field, err in form.errors.items():
          message.append(field + ' ' + '|'.join(err))
      flash('Errors '+ str(message))

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
  #NO POINT IN GETTING THE NUMBER OF SHOWS BECUASE NOTHING IS DONE WITH IT IN THE VIEW
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

@app.route('/shows/search', methods=['POST'])
def search_shows():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    error = False
    try:
        show_data = []
        data = []
        search_term = request.form.get('search_term', '')
        venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
        count = 0
        for venue in venues:
            shows = Shows.query.filter_by(venue_id=venue.id).all()
            count += len(shows)
            for show in shows:
                artist = Artist.query.get(show.artist_id)
                show_data.append({
                    'show_id': show.id,
                    'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M"),
                    'artist_id' : artist.id,
                    'artist_name' : artist.name,
                    'artist_image_link' : artist.image_link,
                    'venue_id' : venue.id,
                    'venue_name' : venue.name
                })
        response = {
            'count': count,
            'data': show_data,
        }
    except Exception as e:
        print('Error retrieving search data: ',e)
        error = True
    finally:
        if error:
            abort(500)
        else:
            print(response)
            return render_template('pages/search_shows.html', results=response, search_term=search_term)

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
