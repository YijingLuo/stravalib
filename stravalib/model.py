"""
Entity classes for representing the various Strava datatypes. 
"""
import abc
import logging
from datetime import datetime
from collections import namedtuple

from stravalib import exc
from stravalib import unithelper as uh

from stravalib.attributes import (META, SUMMARY, DETAILED, Attribute, 
                                  TimestampAttribute, LocationAttribute, EntityCollection, 
                                  EntityAttribute, TimeIntervalAttribute, TimezoneAttribute)

class BaseEntity(object):
    """
    A base class for all entities in the system.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, **kwargs):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.from_dict(kwargs)
        
    def from_dict(self, d):
        """
        Populates this object from specified dict.
        
        Only defined attributes will be set; warnings will be logged for invalid attributes.
        """
        for (k,v) in d.items():
            # Only set defined attributes.
            if hasattr(self.__class__, k):
                self.log.debug("Setting attribute {0} on entity {1} with value {2}".format(k, self, v))
                setattr(self, k, v)
            else:
                self.log.warning("No such attribute {0} on entity {1}".format(k, self))
    
    @classmethod
    def deserialize(cls, v):
        """
        Creates a new object based on serialized (dict) struct. 
        """
        o = cls()
        o.from_dict(v)
        return o
    
    def __repr__(self):
        attrs = []
        if hasattr(self.__class__, 'id'):
            attrs.append('id={0}'.format(self.id))
        if hasattr(self.__class__, 'name'):
            attrs.append('name={0!r}'.format(self.name))
        if hasattr(self.__class__, 'resource_state'):
            attrs.append('resource_state={0}'.format(self.resource_state))
            
        return '<{0} {1}>'.format(self.__class__.__name__, ' '.join(attrs))

class ResourceStateEntity(BaseEntity):
    """
    A base class for all entities in the system.
    """
    resource_state = Attribute(int, (META,SUMMARY,DETAILED))
    
class IdentifiableEntity(ResourceStateEntity):
    """
    A base class for all entities in the system.
    """
    id = Attribute(int, (META,SUMMARY,DETAILED))
    
class BoundEntity(BaseEntity):
    """
    The base class for entities that support lazy loading additional data using a bound client.
    """
    
    bind_client = None
    
    def __init__(self, bind_client=None, **kwargs):
        """
        Base entity initializer, which accepts a client parameter that creates a "bound" entity
        which can perform additional lazy loading of content.
        
        :param bind_client: The client instance to bind to this entity.
        :type bind_client: :class:`stravalib.simple.Client`
        """
        self.bind_client = bind_client
        super(BoundEntity, self).__init__(**kwargs)

    @classmethod
    def deserialize(cls, v, bind_client=None):
        """
        Creates a new object based on serialized (dict) struct. 
        """
        o = cls(bind_client=bind_client)
        o.from_dict(v)
        return o

    
    def assert_bind_client(self):
        if self.bind_client is None:
            raise exc.UnboundEntity("Unable to fetch objects for unbound {0} entity.".format(self.__class__))

class LoadableEntity(BoundEntity, IdentifiableEntity):
        
    def hydrate(self):
        """
        Fill this object with data from the bound client.
        
        This default implementation assumes things about the names of methods in the client, so
        may need to be overridden by subclasses.
        """
        if not self.bind_client:
            raise exc.UnboundEntity("Cannot set entity attributes for unbound entity.")
        raise NotImplementedError()
        # TODO: Decided whether we want to keep this
        assumed_method_name = '_populate_{0}'.format(self.__class__.__name__.lower())
        method = getattr(self.bind_client, assumed_method_name)
        method(self.id, self)

class Club(LoadableEntity):
    """
    Class to represent a club.
    
    Currently summary and detail resource states have the same attributes.
    """
    name = Attribute(str, (SUMMARY,DETAILED))
    
    @property
    def members(self):
        if self._members is None:
            self.assert_bind_client()
            self._members = self.bind_client.get_club_members(self.id)  
        return self._members

    @property
    def activities(self):
        if self._activities is None:
            self.assert_bind_client()
            self._activities = self.bind_client.get_club_activities(self.id)  
        return self._activities
    
class Bike(IdentifiableEntity):
    """
    
    """
    id = Attribute(str, (META,SUMMARY,DETAILED))
    name = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED))
    primary = Attribute(bool, (SUMMARY,DETAILED))
    
class Shoe(IdentifiableEntity):
    """
    
    """
    id = Attribute(str, (META,SUMMARY,DETAILED))
    name = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED))
    primary = Attribute(bool, (SUMMARY,DETAILED))
    
class Athlete(LoadableEntity):
    """
    Represents a Strava athlete.
    """
    firstname = Attribute(str, (SUMMARY,DETAILED))
    lastname = Attribute(str, (SUMMARY,DETAILED))
    profile_medium = Attribute(str, (SUMMARY,DETAILED)) # URL to a 62x62 pixel profile picture
    profile = Attribute(str, (SUMMARY,DETAILED)) # URL to a 124x124 pixel profile picture
    city = Attribute(str, (SUMMARY,DETAILED))
    state = Attribute(str, (SUMMARY,DETAILED))
    sex = Attribute(str, (SUMMARY,DETAILED)) # 'M', 'F' or null
    friend = Attribute(str, (SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' the authenticated athlete's following status of this athlete
    follower = Attribute(str, (SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' this athlete's following status of the authenticated athlete
    preimum = Attribute(bool, (SUMMARY,DETAILED)) # true/false
    
    created_at = TimestampAttribute((SUMMARY,DETAILED)) # time string
    updated_at = TimestampAttribute((SUMMARY,DETAILED)) # time string
    
    follower_count = Attribute(int, (DETAILED,))
    friend_count = Attribute(int, (DETAILED,))
    mutual_friend_count = Attribute(int, (DETAILED,))
    date_preference = Attribute(str, (DETAILED,)) # "%m/%d/%Y"
    measurement_preference = Attribute(str, (DETAILED,)) # "feet" (or what "meters"?)
    
    clubs = EntityCollection(Club, (DETAILED,))
    bikes = EntityCollection(Bike, (DETAILED,))
    shoes = EntityCollection(Shoe, (DETAILED,))

    
class ActivityComment(LoadableEntity):
    activity_id = Attribute(int, (META,SUMMARY,DETAILED))
    text = Attribute(str, (META,SUMMARY,DETAILED))
    created_at = TimestampAttribute((SUMMARY,DETAILED))
    
    athlete = None
    # 'athlete' is a summary-level representation of commenter

class Map(IdentifiableEntity):
    id = Attribute(str, (SUMMARY,DETAILED))
    polyline = Attribute(str, (SUMMARY,DETAILED))
    summary_polyline = Attribute(str, (SUMMARY,DETAILED))

class BaseSplit(BaseEntity):
    pass
    # Consider pushing up attribs from MetricSplit and StandardSplit (challenge is in class-level specification of units)

class MetricSplit(BaseSplit):  # This is not a BaseEntity, since there is no id or resource_state ... maybe we need a simpler Base?
    """
    A metric-unit split.
    """
    
    distance = Attribute(float, units=uh.meters)
    elapsed_time = Attribute(int, units=uh.seconds)
    elevation_difference = Attribute(float, units=uh.meters) 
    moving_time = Attribute(int, units=uh.seconds)
    split = Attribute(int)

class StandardSplit(BaseSplit):  # This is not a BaseEntity, since there is no id or resource_state ... maybe we need a simpler Base?
    """
    A standard-unit (not metric) split.
    """
    distance = Attribute(float, units=uh.feet)
    elapsed_time = Attribute(int, units=uh.seconds)
    elevation_difference = Attribute(float, units=uh.feet) 
    moving_time = Attribute(int, units=uh.seconds)
    split = Attribute(int)

class Segment(LoadableEntity):
    """
    """
    name = Attribute(str, (SUMMARY,DETAILED))
    activity_type = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    average_grade = Attribute(float, (SUMMARY,DETAILED)) # percent
    maximum_grade = Attribute(float, (SUMMARY,DETAILED)) # percent
    elevation_high = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    elevation_low = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    start_latlng = LocationAttribute((SUMMARY,DETAILED))
    end_latlng = LocationAttribute((SUMMARY,DETAILED))
    start_latitude = Attribute(float, (SUMMARY,DETAILED))
    end_latitude = Attribute(float, (SUMMARY,DETAILED))
    start_longitude = Attribute(float, (SUMMARY,DETAILED))
    end_longitude = Attribute(float, (SUMMARY,DETAILED))
    climb_category = Attribute(int, (SUMMARY,DETAILED)) # 0-5, lower is harder
    city = Attribute(str, (SUMMARY,DETAILED))
    state = Attribute(str, (SUMMARY,DETAILED))
    private = Attribute(bool, (SUMMARY,DETAILED))
    
    # detailed attribs
    created_at = TimestampAttribute((DETAILED,))
    updated_at = TimestampAttribute((DETAILED,))
    total_elevation_gain = Attribute(float, (DETAILED,), units=uh.meters)
    map = EntityAttribute(Map, (DETAILED,))
    effort_count = Attribute(int, (DETAILED,))
    athlete_count = Attribute(int, (DETAILED,))
    hazardous = Attribute(bool, (DETAILED,))
    pr_time = Attribute(int, (DETAILED,), units=uh.seconds)
    pr_distance = Attribute(float, (DETAILED,), units=uh.meters)
    starred = Attribute(bool, (DETAILED,))
    
class BaseEffort(LoadableEntity):
    name = Attribute(str, (SUMMARY,DETAILED))
    segment = EntityAttribute(Segment, (SUMMARY,DETAILED))
    activity = EntityAttribute("Activity", (SUMMARY,DETAILED))
    athlete = EntityAttribute(Athlete, (SUMMARY,DETAILED))
    kom_rank = Attribute(int, (SUMMARY,DETAILED))
    pr_rank = Attribute(int, (SUMMARY,DETAILED))
    moving_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    elapsed_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED))
    distance = Attribute(int, (SUMMARY,DETAILED), units=uh.meters)

class BestEffort(BaseEffort):
    pass

class SegmentEffort(BaseEffort):
    start_index = Attribute(int, (SUMMARY,DETAILED)) # the activity stream index of the start of this effort
    end_index = Attribute(int, (SUMMARY,DETAILED)) # the activity stream index of the end of this effort
                    
class Activity(LoadableEntity):
    """
    
    """
    guid = Attribute(str, (SUMMARY,DETAILED)) # An undocumented attribute
    
    external_id = Attribute(str, (SUMMARY,DETAILED))
    upload_id = Attribute(str, (SUMMARY,DETAILED))
    athlete = None # META-level
    name = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    moving_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    elapsed_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    total_elevation_gain = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    type = Attribute(str, (SUMMARY,DETAILED))
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED))
    timezone = TimezoneAttribute((SUMMARY,DETAILED))
    start_latlng = LocationAttribute((SUMMARY,DETAILED))
    end_latlng = LocationAttribute((SUMMARY,DETAILED))
    
    location_city = Attribute(str, (SUMMARY,DETAILED)),
    location_state = Attribute(str, (SUMMARY,DETAILED)),
    start_latitude = Attribute(float, (SUMMARY,DETAILED)),
    start_longitude = Attribute(float, (SUMMARY,DETAILED)),
    
    achievement_count = Attribute(int, (SUMMARY,DETAILED)),
    kudos_count = Attribute(int, (SUMMARY,DETAILED)),
    comment_count = Attribute(int, (SUMMARY,DETAILED)),
    athlete_count = Attribute(int, (SUMMARY,DETAILED)),
    photo_count = Attribute(int, (SUMMARY,DETAILED)),
    map = EntityAttribute(Map, (SUMMARY,DETAILED))
    
    trainer = Attribute(bool, (SUMMARY,DETAILED))
    commute = Attribute(bool, (SUMMARY,DETAILED))
    manual = Attribute(bool, (SUMMARY,DETAILED))
    private = Attribute(bool, (SUMMARY,DETAILED))
    flagged = Attribute(bool, (SUMMARY,DETAILED))
    
    _gear = None
    gear_id = Attribute(str, (SUMMARY,DETAILED))
    
    average_speed = Attribute(float, (SUMMARY,DETAILED)) # meters/sec
    max_speed = Attribute(float, (SUMMARY,DETAILED)) # meters/sec
    calories = Attribute(float, (SUMMARY,DETAILED)) 
    truncated = Attribute(int, (SUMMARY,DETAILED))
    has_kudoed = Attribute(bool, (SUMMARY,DETAILED))
  
    segment_efforts = EntityCollection(SegmentEffort, (DETAILED,))
    splits_metric = EntityCollection(MetricSplit, (DETAILED,))
    splits_standard = EntityCollection(StandardSplit, (DETAILED,))
    best_efforts = EntityCollection(BestEffort, (DETAILED,))
    
    """
    @property
    def efforts(self):
        if self._efforts is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve efforts for unbound {0} entity.".format(self.__class__))
            else:
                self._efforts = self.bind_client.get_ride_efforts(self.id)  
        return self._efforts
    """
    @property
    def gear(self):
        if self._gear is None:
            self.assert_bind_client()
            if self.gear_id is not None:
                self._gear = self.bind_client.get_gear(self.gear_id)
        return self._gear
        


class SegmentLeaderboard(BoundEntity):
    """
    {
  "effort_count": 7037,
  "entry_count": 7037,
  "entries": [
    {
      "athlete_name": "Jim Whimpey",
      "athlete_id": 123529,
      "athlete_gender": "M",
      "average_hr": 190.519,
      "average_watts": 460.805,
      "distance": 2659.89,
      "elapsed_time": 360,
      "moving_time": 360,
      "start_date": "2013-03-29T13:49:35Z",
      "start_date_local": "2013-03-29T06:49:35Z",
      "activity_id": 46320211,
      "effort_id": 801006623,
      "rank": 1,
      "athlete_profile": "http://pics.com/227615/large.jpg"
    },
    {
      "athlete_name": "Chris Zappala",
      "athlete_id": 11673,
      "athlete_gender": "M",
      "average_hr": null,
      "average_watts": 368.288,
      "distance": 2705.77,
      "elapsed_time": 374,
      "moving_time": 374,
      "start_date": "2012-02-23T14:50:16Z",
      "start_date_local": "2012-02-23T06:50:16Z",
      "activity_id": 4431903,
      "effort_id": 83383918,
      "rank": 2,
      "athlete_profile": "http://pics.com/227615/large.jpg"
    }
  ]
}
    """
    
    
class DistributionBucket(BaseEntity):
    max = Attribute(int)
    min = Attribute(int)
    time = Attribute(int, units=uh.seconds)

class BaseActivityZone(LoadableEntity):
    """
    Base class for activity zones.
    """
    distribution_buckets = EntityCollection(DistributionBucket, (SUMMARY, DETAILED))
    type = Attribute(str, (SUMMARY, DETAILED))
    sensor_based = Attribute(bool, (SUMMARY, DETAILED))
    
class HeartrateActivityZone(BaseActivityZone):
    score = Attribute(int, (SUMMARY, DETAILED))
    points = Attribute(int, (SUMMARY, DETAILED))
    custom_zones = Attribute(bool, (SUMMARY, DETAILED))
    max = Attribute(int, (SUMMARY, DETAILED))
    
class PowerActivityZone(BaseActivityZone):
    bike_weight = Attribute(float, (SUMMARY, DETAILED), units=uh.kgs)
    athlete_weight = Attribute(float, (SUMMARY, DETAILED), units=uh.kgs)