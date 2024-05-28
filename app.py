#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import and_, distinct, func, or_
from forms import *
from CityState import CityState
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  #replace with real venues data.
  #num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  results = db.session.query(Venue.city, Venue.state).distinct().all()

  list_city_and_state = [CityState(city=city, state=state) for city, state in results]

  # Get the current time
  current_time = datetime.now()

  for city_state in list_city_and_state:
      city_state.venues = db.session.query(
      Venue.id,
      Venue.name,
      func.count(Show.id).label('upcoming_show_count')).outerjoin(
      Show, 
      and_(Venue.id == Show.venue_id, Show.start_time > current_time)).filter(
          Venue.city == city_state.city,
          Venue.state == city_state.state).group_by(Venue.id, Venue.name).all()
  
  return render_template('pages/venues.html', areas=list_city_and_state)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  #implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form['search_term'].lower()

  venueQuery = db.session.query(Venue.id, Venue.name).filter(
      func.lower(Venue.name).contains(search_term)
  )

  data = venueQuery.all()
  count = venueQuery.count()

  response={
    "count": count,
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  #replace with real venue data from the venues table, using venue_id
  query = db.session.query(Venue).filter(Venue.id == venue_id)
  data = query.first()

  # Get the current time
  current_time = datetime.now()

  past_shows_query = db.session.query(Artist.id.label('artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), func.to_char(Show.start_time, 'YYYY-MM-DD HH24:MI:SS').label('start_time')).filter(Show.venue_id == venue_id).join(Artist, Artist.id == Show.artist_id).filter(Show.start_time < current_time)
  past_shows = past_shows_query.all()
  past_shows_count = past_shows_query.count()

  up_coming_shows_query = db.session.query(Artist.id.label('artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), func.to_char(Show.start_time, 'YYYY-MM-DD HH24:MI:SS').label('start_time')).filter(Show.venue_id == venue_id).join(Artist, Artist.id == Show.artist_id).filter(Show.start_time > current_time)
  up_coming_shows = up_coming_shows_query.all()
  up_coming_shows_count = up_coming_shows_query.count()
  
  if data is not None: 
    result = {
    "id": data.id,
    "name": data.name,
    "genres": data.genres.split(', '),
    "address": data.address,
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website": data.website_link,
    "facebook_link": data.facebook_link,
    "seeking_talent": data.seeking_talent,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": up_coming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": up_coming_shows_count,
  }
  else :
    result = None
    
  return render_template('pages/show_venue.html', venue=result)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  #insert form data as a new Venue record in the db, instead
  #modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  #on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  try:
    form = VenueForm(request.form)
    venue = Venue()
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.address = form.address.data
    genres = form.genres.data
    venue.genres = ', '.join(str(element) for element in genres)
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = 'seeking_talent' in form.data
    venue.seeking_description = form.seeking_description.data
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully listed!')
  except Exception as ex:
    db.session.rollback()
    flash('An error occurred. Venue ' + form.data.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue = db.session.query(Venue).first()
    db.session.delete(venue)
    db.session.commit()
    return venue
  except Exception as ex:
    db.session.rollback()
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  #replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  #implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form['search_term'].lower()

  artistQuery = db.session.query(Artist.id, Artist.name).filter(
      func.lower(Artist.name).contains(search_term)
  )
  artistsCount = artistQuery.count()
  data = artistQuery.all()
  response={
    "count": artistsCount,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # replace with real artist data from the artist table, using artist_id
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id
  query = db.session.query(Artist).filter(Artist.id == artist_id)
  data = query.first()

  # Get the current time
  current_time = datetime.now()

  past_shows_query = db.session.query(Venue.id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), func.to_char(Show.start_time, 'YYYY-MM-DD HH24:MI:SS').label('start_time')).join(Venue, Venue.id == Show.venue_id).filter(Show.start_time < current_time).filter(Show.artist_id == artist_id)
  past_shows = past_shows_query.all()
  past_shows_count = past_shows_query.count()

  up_coming_shows_query = db.session.query(Venue.id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), func.to_char(Show.start_time, 'YYYY-MM-DD HH24:MI:SS').label('start_time')).join(Venue, Venue.id == Show.venue_id).filter(Show.start_time > current_time).filter(Show.artist_id == artist_id)
  up_coming_shows = up_coming_shows_query.all()
  up_coming_shows_count = up_coming_shows_query.count()
  
  if data is not None: 
    result = {
    "id": data.id,
    "name": data.name,
    "genres": data.genres.split(', '),
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website": data.website_link,
    "facebook_link": data.facebook_link,
    "seeking_venue": data.seeking_venue,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": up_coming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": up_coming_shows_count,
  }
  else :
    result = None
  
  return render_template('pages/show_artist.html', artist = result)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  query = db.session.query(Artist).filter(Artist.id == artist_id)
  data = query.first()
  artist = {
    "id": data.id,
    "name": data.name,
    "genres": data.genres.split(', '),
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website_link": data.website_link,
    "facebook_link": data.facebook_link,
    "seeking_venue": data.seeking_venue,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link
  }
  form = ArtistForm(data=artist)
  # populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  #take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  query = db.session.query(Artist).filter(Artist.id == artist_id)
  data = query.first()
  form = ArtistForm(request.form)
  try:
    data.name = form.name.data
    data.city = form.city.data
    data.state = form.state.data
    data.phone = form.phone.data
    genres = form.genres.data
    data.genres = ', '.join(str(element) for element in genres)
    data.facebook_link = form.facebook_link.data
    data.image_link = form.image_link.data
    data.website_link = form.website_link.data
    data.seeking_venue = 'seeking_venue' in form.data
    data.seeking_description = form.seeking_description.data
    db.session.commit()
  except Exception as ex:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  query = db.session.query(Venue).filter(Venue.id == venue_id)
  data = query.first()
  venue = {
    "id": data.id,
    "name": data.name,
    "genres": data.genres.split(', '),
    "address": data.address,
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website_link": data.website_link,
    "facebook_link": data.facebook_link,
    "seeking_talent": data.seeking_talent,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link
  }
  form = VenueForm(data=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  #take values from the form submitted, and update existing
  #venue record with ID <venue_id> using the new attributes
  query = db.session.query(Venue).filter(Venue.id == venue_id)
  data = query.first()
  form = VenueForm(request.form)
  try:
    data.name = form.name.data
    data.city = form.city.data
    data.state = form.state.data
    data.phone = form.phone.data
    data.address = form.address.data
    genres = form.genres.data
    data.genres = ', '.join(str(element) for element in genres)
    data.facebook_link = form.facebook_link.data
    data.image_link = form.image_link.data
    data.website_link = form.website_link.data
    data.seeking_talent = 'seeking_talent' in form.data
    data.seeking_description = form.seeking_description.data
    db.session.commit()
  except Exception as ex:
    db.session.rollback()
  finally:
    db.session.close()
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
  #insert form data as a new Venue record in the db, instead
  #modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  #on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  try:
    form = ArtistForm(request.form)
    artist = Artist()
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    genres = form.genres.data
    artist.genres = ', '.join(str(element) for element in genres)
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = True if form.seeking_venue.data == 'y' else False
    artist.seeking_description = form.seeking_description.data
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + form.name.data + ' was successfully listed!')
  except Exception as ex:
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # replace with real venues data.
  shows_query = db.session.query(Show.venue_id, Venue.name.label('venue_name'), Show.artist_id, Artist.image_link.label('artist_image_link'), Artist.name.label('artist_name'), func.to_char(Show.start_time, 'YYYY-MM-DD HH24:MI:SS').label('start_time')).join(Venue, Venue.id == Show.venue_id).join(Artist, Artist.id == Show.artist_id)
  data = shows_query.all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  #called to create new shows in the db, upon submitting new show listing form
  #insert form data as a new Show record in the db, instead

  #on successful db insert, flash success
  #flash('Show was successfully listed!')
  #on unsuccessful db insert, flash an error instead.
  #e.g., flash('An error occurred. Show could not be listed.')
  #see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

  form = ShowForm(request.form)
  try:
    show = Show()
    show.artist_id = form.artist_id.data
    show.venue_id = form.venue_id.data
    show.start_time = form.start_time.data
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as ex:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/shows/search', methods=['GET'])
def search_shows():
  return render_template('pages/show.html')

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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
