#!/usr/bin/env python3
"""
Complete UFC Rankings Update Script
Updates database with champions and full top 10 rankings for all divisions
Data accurate as of January 2025
"""

import sqlite3
from datetime import datetime
import sys
import os

# Add the parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def update_full_rankings():
    """Update UFC rankings with champions and complete top 10 for all divisions"""

    rankings_data = [
        # HEAVYWEIGHT
        {'division': 'Heavyweight', 'fighter_name': 'Tom Aspinall', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Ciryl Gane', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Alexander Volkov', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Sergei Pavlovich', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Curtis Blaydes', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Jailton Almeida', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Waldo Cortes Acosta', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Serghei Spivac', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Derrick Lewis', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Ante Delija', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Heavyweight', 'fighter_name': 'Marcin Tybura', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # LIGHT HEAVYWEIGHT
        {'division': 'Light Heavyweight', 'fighter_name': 'Alex Pereira', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Jiří Procházka', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Magomed Ankalaev', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Carlos Ulberg', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Khalil Rountree Jr.', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Jan Błachowicz', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Jamahal Hill', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Azamat Murzakanov', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Dominick Reyes', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Volkan Oezdemir', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Aleksandar Rakić', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # MIDDLEWEIGHT
        {'division': 'Middleweight', 'fighter_name': 'Khamzat Chimaev', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Dricus Du Plessis', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Nassourdine Imavov', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Sean Strickland', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Anthony Hernandez', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Brendan Allen', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Israel Adesanya', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Caio Borralho', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Reinier de Ridder', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Robert Whittaker', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Jared Cannonier', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # WELTERWEIGHT
        {'division': 'Welterweight', 'fighter_name': 'Jack Della Maddalena', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Belal Muhammad', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Sean Brady', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Shavkat Rakhmonov', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Leon Edwards', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Kamaru Usman', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Ian Machado Garry', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Joaquin Buckley', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Michael Morales', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Carlos Prates', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Gabriel Bonfim', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # LIGHTWEIGHT
        {'division': 'Lightweight', 'fighter_name': 'Ilia Topuria', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Islam Makhachev', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Arman Tsarukyan', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Charles Oliveira', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Max Holloway', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Justin Gaethje', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Paddy Pimblett', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Dan Hooker', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Mateusz Gamrot', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Beneil Dariush', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Rafael Fiziev', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # FEATHERWEIGHT
        {'division': 'Featherweight', 'fighter_name': 'Alexander Volkanovski', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Movsar Evloev', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Diego Lopes', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Yair Rodriguez', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Lerone Murphy', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Aljamain Sterling', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Arnold Allen', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Youssef Zalal', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Steve Garcia', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Brian Ortega', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Josh Emmett', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # BANTAMWEIGHT
        {'division': 'Bantamweight', 'fighter_name': 'Merab Dvalishvili', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Umar Nurmagomedov', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': "Sean O'Malley", 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Petr Yan', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Cory Sandhagen', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Song Yadong', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Deiveson Figueiredo', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Aiemann Zahabi', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Marlon Vera', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Mario Bautista', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Henry Cejudo', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # FLYWEIGHT
        {'division': 'Flyweight', 'fighter_name': 'Alexandre Pantoja', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Joshua Van', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Brandon Moreno', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Brandon Royval', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Amir Albazi', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Tatsuro Taira', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Kai Kara-France', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Manel Kape', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Alex Perez', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Asu Almabayev', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Tim Elliott', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # WOMEN'S BANTAMWEIGHT
        {'division': "Women's Bantamweight", 'fighter_name': 'Kayla Harrison', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Julianna Peña', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Raquel Pennington', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Norma Dumont', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Ketlen Vieira', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Yana Santos', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Irene Aldana', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Macy Chiasson', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Ailin Perez', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Karol Rosa', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Jacqueline Cavalcanti', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},

        # WOMEN'S FLYWEIGHT
        {'division': "Women's Flyweight", 'fighter_name': 'Valentina Shevchenko', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Manon Fiorot', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Natalia Silva', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Alexa Grasso', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Erin Blanchfield', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Maycee Barber', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Rose Namajunas', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Jasmine Jasudavicius', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Tracy Cortez', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Karine Silva', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Miranda Maverick', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},

        # WOMEN'S STRAWWEIGHT
        {'division': "Women's Strawweight", 'fighter_name': 'Mackenzie Dern', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Tatiana Suarez', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Zhang Weili', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Virna Jandiroba', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Yan Xiaonan', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Amanda Lemos', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Loopy Godinez', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Iasmin Lucindo', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Tabatha Ricci', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Jéssica Andrade', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Gillian Robertson', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},

        # POUND FOR POUND
        {"division": "Men's P4P", 'fighter_name': 'Ilia Topuria', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {"division": "Men's P4P", 'fighter_name': 'Alex Pereira', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {"division": "Men's P4P", 'fighter_name': 'Islam Makhachev', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {"division": "Men's P4P", 'fighter_name': 'Jon Jones', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {"division": "Men's P4P", 'fighter_name': 'Merab Dvalishvili', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {"division": "Women's P4P", 'fighter_name': 'Valentina Shevchenko', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
        {"division": "Women's P4P", 'fighter_name': 'Zhang Weili', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
        {"division": "Women's P4P", 'fighter_name': 'Kayla Harrison', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
    ]

    db_path = "data/mma.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False

    try:
        print("🚀 Updating UFC Rankings with Complete Data...")
        print("=" * 50)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clear existing rankings
        cursor.execute("DELETE FROM ufc_rankings")
        print("🗑️  Cleared existing rankings")

        # Insert new rankings
        inserted_count = 0
        champions_count = 0

        for ranking in rankings_data:
            cursor.execute("""
                INSERT INTO ufc_rankings
                (division, fighter_name, rank, is_champion, is_interim_champion,
                 gender, ranking_type, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ranking['division'],
                ranking['fighter_name'],
                ranking['rank'],
                ranking['is_champion'],
                ranking['is_interim_champion'],
                ranking['gender'],
                ranking['ranking_type'],
                datetime.now()
            ))

            if ranking['is_champion']:
                champions_count += 1
            inserted_count += 1

        conn.commit()
        conn.close()

        print(f"✅ Successfully updated database:")
        print(f"   📊 {inserted_count} total entries")
        print(f"   🏆 {champions_count} champions")
        print(f"   🥊 Top 10 rankings for all divisions")
        print(f"   👑 {len([r for r in rankings_data if r['ranking_type'] == 'P4P'])} P4P rankings")
        print("=" * 50)
        print("🏁 Rankings update completed successfully!")

        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    success = update_full_rankings()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
