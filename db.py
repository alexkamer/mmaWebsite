from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, create_engine, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship, Session
from datetime import datetime
from typing import Union, List, Dict, Any
from sqlalchemy.exc import IntegrityError

Base = declarative_base()

class League(Base):
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, doc="The id of the league")
    name = Column(String, doc="The name of the league")
    displayName = Column(String, doc="The display name of the league")
    logo = Column(String, doc="The logo of the league")


class Athlete(Base):
    __tablename__ = "athletes"
    
    id = Column(Integer, primary_key=True, doc="The id of the athlete")
    uid = Column(String, doc="The uid of the athlete")
    guid = Column(String, doc="The guid of the athlete")
    first_name = Column(String, doc="The first name of the athlete")
    last_name = Column(String, doc="The last name of the athlete")
    full_name = Column(String, doc="The full name of the athlete")
    display_name = Column(String, doc="The display name of the athlete")
    nickname = Column(String, doc="The nickname of the athlete")
    short_name = Column(String, doc="The short name of the athlete")
    weight = Column(String, doc="The weight of the athlete")
    display_weight = Column(String, doc="The display weight of the athlete")
    height = Column(String, doc="The height of the athlete")
    display_height = Column(String, doc="The display height of the athlete")
    age = Column(Integer, doc="The age of the athlete")
    date_of_birth = Column(String, doc="The date of birth of the athlete")
    gender = Column(String, doc="The gender of the athlete")
    is_active = Column(Boolean, doc="Whether the athlete is active")
    status = Column(String, doc="The status of the athlete")
    stance = Column(String, doc="The stance of the athlete")
    reach = Column(String, doc="The reach of the athlete")
    weight_class = Column(String, doc="The weight class of the athlete")
    weight_class_slug = Column(String, doc="The weight class slug of the athlete")
    association = Column(String, doc="The association of the athlete")
    association_city = Column(String, doc="The association city of the athlete")
    default_league = Column(String, doc="The default league of the athlete")
    flag_url = Column(String, doc="The flag url of the athlete")
    headshot_url = Column(String, doc="The headshot url of the athlete")

class Card(Base):
    __tablename__ = "cards"
    year_league_event_id_event_name = Column(String, doc="The year league event id and event name of the card", primary_key=True)
    event_id = Column(Integer, doc="The event id of the card")
    league = Column(String, doc="The league of the card")
    event_name = Column(String, doc="The event name of the card")
    date = Column(DateTime, doc="The date of the card")
    venue_id = Column(Integer, doc="The venue id of the card")
    venue_name = Column(String, doc="The venue name of the card")
    country = Column(String, doc="The country of the card")
    state = Column(String, doc="The state of the card")
    city = Column(String, doc="The city of the card")

class Fight(Base):

    __tablename__ = "fights"
    year_league_event_id_fight_id_f1_f2 = Column(String, doc="The year league event id and fight id of the fight", primary_key=True)
    fight_title = Column(String, doc="The title of the fight")
    boxscoreAvailable = Column(Boolean, doc="Whether the boxscore is available")
    playByPlayAvailable = Column(Boolean, doc="Whether the play by play is available")
    summaryAvailable = Column(Boolean, doc="Whether the summary is available")
    
    event_id_fight_id = Column(String, doc="The event id and fight id of the fight")
    league = Column(String, doc="The league of the fight")
    event_id = Column(Integer, doc="The event id of the fight")
    fight_id = Column(Integer, doc="The fight id of the fight")
    odds_url = Column(String, doc="The odds url of the fight")
    officials_url = Column(String, doc="The officials url of the fight")
    rounds_format = Column(Integer, doc="The rounds format of the fight")
    seconds_per_round = Column(Float, doc="The seconds per round of the fight")
    match_number = Column(Integer, doc="The match number of the fight")
    card_segment = Column(String, doc="The card segment of the fight")
    weight_class_id = Column(Integer, doc="The weight class id of the fight")
    weight_class = Column(String, doc="The weight class of the fight")
    end_round = Column(Integer, doc="The round of the fight")
    end_time = Column(String, doc="The time of the fight")
    result_display_name = Column(String, doc="The result display name of the fight")
    fighter_1_id = Column(Integer, doc="The id of the first fighter in the fight")
    fighter_1_winner = Column(Boolean, doc="Whether the first fighter won the fight")
    fighter_1_linescore = Column(String, doc="The linescore of the first fighter")
    fighter_1_statistics = Column(String, doc="The statistics of the first fighter")
    fighter_2_id = Column(Integer, doc="The id of the second fighter in the fight")
    fighter_2_winner = Column(Boolean, doc="Whether the second fighter won the fight")
    fighter_2_linescore = Column(String, doc="The linescore of the second fighter")
    fighter_2_statistics = Column(String, doc="The statistics of the second fighter")


class Odds(Base):
    __tablename__ = "odds"

    provider_id_fight_id = Column(String, doc="The provider id and fight id of the odds", primary_key=True)
    fight_id = Column(String, doc="The fight id of the odds")
    provider_id = Column(Integer, doc="The id of the provider")
    provider_name = Column(String, doc="The name of the provider")
    details = Column(String, doc="The details of the odds")
    away_athlete_id = Column(String, doc="The id of the away athlete")
    away_favorite = Column(Boolean, doc="Whether the away athlete is the favorite")
    away_underdog = Column(Boolean, doc="Whether the away athlete is the underdog")
    away_moneyLine_odds = Column(Float, doc="The money line odds of the away athlete")
    away_moneyLine_odds_current_american = Column(String, doc="The current american odds of the away athlete")
    away_moneyLine_odds_current_decimal = Column(Float, doc="The current decimal odds of the away athlete")
    away_moneyLine_odds_current_fractional = Column(String, doc="The current fractional odds of the away athlete")
    away_moneyLine_odds_current_value = Column(Float, doc="The current value of the away athlete's money line odds")
    away_victoryMethod_koTkoDq_value = Column(Float, doc="The value of the away athlete's victory method (ko/tko/dq)")
    away_victoryMethod_koTkoDq_american = Column(String, doc="The american format of the away athlete's victory method (ko/tko/dq)")
    away_victoryMethod_koTkoDq_decimal = Column(Float, doc="The decimal format of the away athlete's victory method (ko/tko/dq)")
    away_victoryMethod_koTkoDq_fractional = Column(String, doc="The fractional format of the away athlete's victory method (ko/tko/dq)")
    away_victoryMethod_submission_value = Column(Float, doc="The value of the away athlete's victory method (submission)")
    away_victoryMethod_submission_american = Column(String, doc="The american format of the away athlete's victory method (submission)")
    away_victoryMethod_submission_decimal = Column(Float, doc="The decimal format of the away athlete's victory method (submission)")
    away_victoryMethod_submission_fractional = Column(String, doc="The fractional format of the away athlete's victory method (submission)")
    away_victoryMethod_points_value = Column(Float, doc="The value of the away athlete's victory method (points)")
    away_victoryMethod_points_american = Column(String, doc="The american format of the away athlete's victory method (points)")
    away_victoryMethod_points_decimal = Column(Float, doc="The decimal format of the away athlete's victory method (points)")
    away_victoryMethod_points_fractional = Column(String, doc="The fractional format of the away athlete's victory method (points)")
    home_athlete_id = Column(String, doc="The id of the home athlete")
    home_favorite = Column(Boolean, doc="Whether the home athlete is the favorite")
    home_underdog = Column(Boolean, doc="Whether the home athlete is the underdog")
    home_moneyLine_odds = Column(Float, doc="The money line odds of the home athlete")
    home_moneyLine_odds_current_american = Column(String, doc="The current american odds of the home athlete")
    home_moneyLine_odds_current_decimal = Column(Float, doc="The current decimal odds of the home athlete")
    home_moneyLine_odds_current_fractional = Column(String, doc="The current fractional odds of the home athlete")
    home_moneyLine_odds_current_value = Column(Float, doc="The current value of the home athlete's money line odds")
    home_victoryMethod_koTkoDq_value = Column(Float, doc="The value of the home athlete's victory method (ko/tko/dq)")
    home_victoryMethod_koTkoDq_american = Column(String, doc="The american format of the home athlete's victory method (ko/tko/dq)")
    home_victoryMethod_koTkoDq_decimal = Column(Float, doc="The decimal format of the home athlete's victory method (ko/tko/dq)")
    home_victoryMethod_koTkoDq_fractional = Column(String, doc="The fractional format of the home athlete's victory method (ko/tko/dq)")
    home_victoryMethod_submission_value = Column(Float, doc="The value of the home athlete's victory method (submission)")
    home_victoryMethod_submission_american = Column(String, doc="The american format of the home athlete's victory method (submission)")
    home_victoryMethod_submission_decimal = Column(Float, doc="The decimal format of the home athlete's victory method (submission)")
    home_victoryMethod_submission_fractional = Column(String, doc="The fractional format of the home athlete's victory method (submission)")
    home_victoryMethod_points_value = Column(Float, doc="The value of the home athlete's victory method (points)")
    home_victoryMethod_points_american = Column(String, doc="The american format of the home athlete's victory method (points)")
    home_victoryMethod_points_decimal = Column(Float, doc="The decimal format of the home athlete's victory method (points)")
    home_victoryMethod_points_fractional = Column(String, doc="The fractional format of the home athlete's victory method (points)")
    rounds_over_under_value = Column(String, doc="The value of the rounds over/under")
    rounds_over_decimal = Column(Float, doc="The decimal format of the rounds over/under")
    rounds_over_fractional = Column(String, doc="The fractional format of the rounds over/under")
    rounds_over_american = Column(String, doc="The american format of the rounds over/under")
    rounds_under_decimal = Column(Float, doc="The decimal format of the rounds under/under")
    rounds_under_fractional = Column(String, doc="The fractional format of the rounds under/under")
    rounds_under_american = Column(String, doc="The american format of the rounds under/under")

class StatisticsForFight(Base):
    __tablename__ = "statistics_for_fights"

    event_competition_athlete_id = Column(String, doc="The event competition athlete id of the statistics", primary_key=True)
    event_id = Column(Integer, doc="The event id of the statistics")
    competition_id = Column(Integer, doc="The competition id of the statistics")
    athlete_id = Column(Integer, doc="The athlete id of the statistics")
    knockDowns = Column(Float, doc="The knockdowns of the statistics")
    totalStrikesAttempted = Column(Float, doc="The total strikes attempted of the statistics")
    totalStrikesLanded = Column(Float, doc="The total strikes landed of the statistics")
    sigStrikesAttempted = Column(Float, doc="The significant strikes attempted of the statistics")
    sigStrikesLanded = Column(Float, doc="The significant strikes landed of the statistics")
    sigDistanceHeadStrikesAttempted = Column(Float, doc="The significant distance head strikes attempted of the statistics")
    sigDistanceHeadStrikesLanded = Column(Float, doc="The significant distance head strikes landed of the statistics")
    sigDistanceBodyStrikesAttempted = Column(Float, doc="The significant distance body strikes attempted of the statistics")
    sigDistanceBodyStrikesLanded = Column(Float, doc="The significant distance body strikes landed of the statistics")
    sigDistanceLegStrikesAttempted = Column(Float, doc="The significant distance leg strikes attempted of the statistics")
    sigDistanceLegStrikesLanded = Column(Float, doc="The significant distance leg strikes landed of the statistics")
    sigClinchBodyStrikesAttempted = Column(Float, doc="The significant clinch body strikes attempted of the statistics")
    sigClinchBodyStrikesLanded = Column(Float, doc="The significant clinch body strikes landed of the statistics")
    sigClinchHeadStrikesAttempted = Column(Float, doc="The significant clinch head strikes attempted of the statistics")
    sigClinchHeadStrikesLanded = Column(Float, doc="The significant clinch head strikes landed of the statistics")
    sigClinchLegStrikesAttempted = Column(Float, doc="The significant clinch leg strikes attempted of the statistics")
    sigClinchLegStrikesLanded = Column(Float, doc="The significant clinch leg strikes landed of the statistics")
    sigGroundHeadStrikesAttempted = Column(Float, doc="The significant ground head strikes attempted of the statistics")
    sigGroundHeadStrikesLanded = Column(Float, doc="The significant ground head strikes landed of the statistics")
    sigGroundBodyStrikesAttempted = Column(Float, doc="The significant ground body strikes attempted of the statistics")
    sigGroundBodyStrikesLanded = Column(Float, doc="The significant ground body strikes landed of the statistics")
    sigGroundLegStrikesAttempted = Column(Float, doc="The significant ground leg strikes attempted of the statistics")
    sigGroundLegStrikesLanded = Column(Float, doc="The significant ground leg strikes landed of the statistics")
    takedownsAttempted = Column(Float, doc="The takedowns attempted of the statistics")
    takedownsLanded = Column(Float, doc="The takedowns landed of the statistics")
    takedownsSlams = Column(Float, doc="The takedowns slams of the statistics")
    takedownAccuracy = Column(Float, doc="The takedown accuracy of the statistics")
    targetBreakdownHead = Column(Float, doc="The target breakdown head of the statistics")
    targetBreakdownBody = Column(Float, doc="The target breakdown body of the statistics")
    targetBreakdownLeg = Column(Float, doc="The target breakdown leg of the statistics")
    posBreakdownDistance = Column(Float, doc="The position breakdown distance of the statistics")
    posBreakdownClinch = Column(Float, doc="The position breakdown clinch of the statistics")
    posBreakdownGround = Column(Float, doc="The position breakdown ground of the statistics")
    advances = Column(Float, doc="The advances of the statistics")
    advanceToHalfGuard = Column(Float, doc="The advance to half guard of the statistics")
    advanceToSide = Column(Float, doc="The advance to side of the statistics")
    advanceToMount = Column(Float, doc="The advance to mount of the statistics")
    advanceToBack = Column(Float, doc="The advance to back of the statistics")
    reversals = Column(Float, doc="The reversals of the statistics")
    submissions = Column(Float, doc="The submissions of the statistics")
    slamRate = Column(Float, doc="The slam rate of the statistics")
    timeInControl = Column(Float, doc="The time in control of the statistics")




def add_to_db(data: Union[Dict[str, Any], List[Dict[str, Any]]], model_class: type) -> None:
    """
    Add one or more records to the database from a dictionary or list of dictionaries.
    Skips any records that would cause integrity errors.
    
    Args:
        data: A dictionary or list of dictionaries containing the data to insert
        model_class: The SQLAlchemy model class to use for insertion
    
    Example:
        # Add a single league
        league_data = {
            "id": 1,
            "name": "UFC",
            "displayName": "UFC",
            "logo": "https://example.com/logo.png"
        }
        add_to_db(league_data, League)
        
        # Add multiple leagues
        leagues_data = [
            {"id": 1, "name": "UFC", "displayName": "UFC", "logo": "https://example.com/logo1.png"},
            {"id": 2, "name": "Bellator", "displayName": "Bellator", "logo": "https://example.com/logo2.png"}
        ]
        add_to_db(leagues_data, League)
    """
    with Session(engine) as session:
        try:
            if isinstance(data, dict):
                # Single record
                try:
                    record = model_class(**data)
                    session.add(record)
                    session.commit()
                    # print(f"Successfully added record to {model_class.__tablename__}")
                except IntegrityError as e:
                    session.rollback()
                    print(f"Skipping duplicate record in {model_class.__tablename__}: {str(e)}")
            else:
                # Multiple records
                successful = 0
                for item in data:
                    try:
                        record = model_class(**item)
                        session.add(record)
                        session.commit()
                        successful += 1
                    except IntegrityError as e:
                        session.rollback()
                        print(f"Skipping duplicate record in {model_class.__tablename__}: {str(e)}")
                        continue
                print(f"Successfully added {successful} out of {len(data)} records to {model_class.__tablename__}")
        except Exception as e:
            session.rollback()
            print(f"Error adding records to {model_class.__tablename__}: {str(e)}")
            raise

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///data/mma.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) 