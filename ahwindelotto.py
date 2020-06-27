"""
usage:
    python ahwindelotto.py

    tells user if lotto won
    given the draw number
    and the number chosen

overview:

"""
from bs4 import BeautifulSoup
import requests
import sqlite3

MAX_LOTTO_NUM = 36
QUERY_STR = 'http://www.nlcbplaywhelotto.com/nlcb-lotto-plus-results/?drawnumber={}'
CROSS = 'x'
CHECK_MARK = u'\u2713'
DB_CONN = 'lotto_numbers.db'  # lotto numbers stored in a database


def main():
    drawnumber = get_draw()
    my_numbers = get_my_numbers()

    """
    1st, check the database to see whether draw exist - return numbers if it does
    otherwise, scrape site for winning numbers, adding these if they exist
    """
    winning_numbers = database_has_draw(drawnumber)
    if not winning_numbers:  # not found in db, so scrape the web, and add numbers found
        print('scraping the web...')
        winning_numbers = scrape_site_for_numbers(QUERY_STR.format(drawnumber))
        winning_numbers_2 = scrape_site_for_numbers_2(QUERY_STR.format(drawnumber))
        print(winning_numbers_2)
        add_numbers_to_db(drawnumber, winning_numbers)

    win_dict = check(winning_numbers, my_numbers)
    # print(win_dict)
    won = False not in win_dict.values()

    if won:
        print('you won')
    else:
        print('you did not win')

    show_nos_won(my_numbers, win_dict, winning_numbers)


def scrape_site_for_numbers(query):
    response = requests.get(query)
    # response = '<Response object with lots of goodies, including a website's text>'

    html = response.text

    soup = BeautifulSoup(html, 'lxml')
    # draw_date = soup.find('div', 'drawDetails').div.text
    # jackpot = soup.find(id='jackpot').text
    numbers = soup.find_all("div", {"class": "lotto-balls"})
    winning_numbers = [number.text for number in numbers]
    powerball = soup.find('div', {"class": "ball yellow-ball"}).text
    winning_numbers.append('P' + powerball)

    return winning_numbers


def scrape_site_for_numbers_2(query):
    response = requests.get(query)
    # response = '<Response object with lots of goodies, including a website's text>'

    html = response.text

    soup = BeautifulSoup(html, 'lxml')
    draw_date = soup.find('div', 'drawDetails').div
    # jackpot = soup.find(id='jackpot').text
    numbers = soup.find_all("div", {"class": "lotto-balls"})
    winning_numbers = [number.text for number in numbers]
    powerball = soup.find('div', {"class": "ball yellow-ball"})
    parent = powerball.parent
    new_line = parent.next_sibling
    jackpot = new_line.next_sibling
    no_of_winners = jackpot.next_sibling
    winning_numbers.append('P' + powerball.text)

    return winning_numbers, draw_date.text, jackpot.text, no_of_winners.text


def show_nos_won(my_numbers, win_dict, winning_numbers):
    print('{:<20}'.format('Winning numbers'), end='')
    for number in winning_numbers:
        print('{:>2} '.format(number), end='')

    print()
    print('{:<20}'.format('Your numbers'), end='')
    for number in my_numbers:
        print('{:>2} '.format(number), end='')
    print()

    print('{:<20}'.format(' '), end='')
    for number in my_numbers:
        if win_dict[number]:
            print('{:>2} '.format(CHECK_MARK), end='')
        else:
            print('{:>2} '.format(CROSS), end='')
    print()


def database_has_draw(drawnumber):
    """
    returns winning_number as list if found
    otherwise returns empty list
    """
    winning_numbers = []
    conn = sqlite3.connect(DB_CONN)
    results = conn.execute('select draw_numer, ball_1, ball_2, ball_3, ball_4, ball_5, power_ball from draw_numbers where draw_numer = {}'.format(drawnumber))
    for cursor in results:
        winning_numbers = list(cursor[1:])
        winning_numbers[5] = 'P' + str(winning_numbers[5])

    conn.close()

    winning_numbers = [str(number) for number in winning_numbers]

    return winning_numbers


def add_numbers_to_db(drawnumber, winning_numbers):
    """
    add drawnumber and winning_numbers to db
    """
    conn = sqlite3.connect(DB_CONN)
    exec_str = 'insert into draw_numbers (draw_numer, ball_1, ball_2, ball_3, ball_4, ball_5, power_ball) values ({}, {}, {}, {}, {}, {}, {})'.format(drawnumber, winning_numbers[0], winning_numbers[1], winning_numbers[2], winning_numbers[3], winning_numbers[4], winning_numbers[5].replace('P', ''))
    print(exec_str)
    conn.execute(exec_str)
    conn.commit()
    conn.close()


def check(winning_numbers, my_numbers):
    """
        returns a dictionary with key as your numbers
        and values as True or False
    """

    return {number: number in winning_numbers for number in my_numbers}


def get_draw():
    return input('Enter draw number #: ')


def get_my_numbers():
    return input('Enter your numbers: ').split(' ')


if __name__ == '__main__':
    main()
