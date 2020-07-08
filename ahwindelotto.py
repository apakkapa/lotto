"""
usage:
    python ahwindelotto.py

    tells user if lotto won
    given the draw_number
    and the numbers chosen

overview:
"""

from bs4 import BeautifulSoup
import requests
import sqlite3
import datetime
import sys

MAX_LOTTO_NUM = 36
QUERY_STR = 'http://www.nlcbplaywhelotto.com/nlcb-lotto-plus-results/?drawnumber={}'
CROSS = 'x'
CHECK_MARK = u'\u2713'
DB_CONN = 'lotto_numbers.db'  # lotto numbers stored in a database


def main():
    if len(sys.argv) > 1:
        print('adding data')
        no = int(sys.argv[1])
        scrape_and_add(no)
        return None

    draw_number = get_draw()
    my_numbers = get_my_numbers()

    """
    1st, check the database to see whether draw exist - return numbers if it does
    otherwise, scrape site for winning numbers, adding these if they exist
    """
    winning_numbers, draw_date, draw_jackpot, no_of_winners = database_has_draw(draw_number)

    if not winning_numbers:  # not found in db, so scrape the web, and add numbers found
        print('scraping the web...')
        # winning_numbers = scrape_site_for_numbers(QUERY_STR.format(draw_number))
        winning_numbers, draw_date, draw_jackpot, no_of_winners = scrape_site_for_numbers(QUERY_STR.format(draw_number))
        # return winning_numbers, draw_date.text, jackpot.text, no_of_winners.text
        add_numbers_to_db(draw_number, winning_numbers, draw_date, draw_jackpot, no_of_winners)

    win_dict = check(winning_numbers, my_numbers)
    # print(win_dict)
    won = False not in win_dict.values()

    if won:
        print('you won')
    else:
        print('you did not win')

    show_nos_won(my_numbers, win_dict, winning_numbers, draw_number, draw_date, draw_jackpot, no_of_winners)


def scrape_and_add(start_no):
    for draw_no in range(start_no, 1952):
        query = QUERY_STR.format(draw_no)
        winning_numbers_2, draw_date, draw_jackpot, no_of_winners = scrape_site_for_numbers(query)
        print(winning_numbers_2, draw_date, draw_jackpot, no_of_winners)
        add_numbers_to_db(draw_no, winning_numbers_2, draw_date, draw_jackpot, no_of_winners)


def scrape_site_for_numbers(query):
    def after_colon(s):
        colon_pos = s.find(':')
        return s[colon_pos + 1:]

    def actual_value(var, var_type, default):
        if var and hasattr(var, var_type):
            return after_colon(var.text)
        else:
            return default


    response = requests.get(query)
    # response = '<Response object with lots of goodies, including a website's text>'

    html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    draw_date = soup.find('div', {'class': 'drawDetails'}).div
    draw_date_s = actual_value(draw_date, 'text', '1-Jan-01')

    numbers = soup.find_all("div", {"class": "lotto-balls"})
    winning_numbers = [number.text for number in numbers]
    power_ball = soup.find('div', {"class": "ball yellow-ball"})
    parent = power_ball.parent
    new_line = parent.next_sibling

    #  the jackpot may or may not be there
    jackpot = new_line.next_sibling
    no_of_winners = jackpot.next_sibling
    jackpot_s = actual_value(jackpot, 'text', 0)
    no_of_winners_s = actual_value(no_of_winners, 'text', 0)

    winning_numbers.append('P' + power_ball.text)
    return winning_numbers, draw_date_s, jackpot_s, no_of_winners_s


def show_nos_won(my_numbers, win_dict, winning_numbers, draw_number, draw_date, jackpot, no_of_winners):
    print('{}: {} Jackpot:{} No. of winners({})'.format(draw_number, draw_date, jackpot, no_of_winners))
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


def database_has_draw(draw_number):
    """ returns winning_number as list if found
    otherwise returns empty list """
    winning_numbers = []
    conn = sqlite3.connect(DB_CONN)
    draw_date, draw_jackpot, draw_winners = None, None, None
    results = conn.execute("""select draw_no,
                            ball_1,
                            ball_2,
                            ball_3,
                            ball_4,
                            ball_5,
                            power_ball,
                            draw_date,
                            draw_jackpot,
                            draw_winners
                            from draws
                            where draw_no = ?""", (draw_number,))

    for cursor in results:
        winning_numbers = list(cursor[1:7])
        winning_numbers[5] = 'P' + str(winning_numbers[5])
        draw_date = cursor[7]
        draw_jackpot = cursor[8]
        draw_winners = cursor[9]

    conn.close()

    winning_numbers = [str(number) for number in winning_numbers]

    return winning_numbers, draw_date, draw_jackpot, draw_winners


def add_numbers_to_db(draw_number, winning_numbers, draw_date, jackpot, no_of_winners):
    """
    add draw_number and winning_numbers to db
    """

    def strip_chars(s, chars):
        for ch in chars:
            s = s.replace(ch, '')
        return s

    plain_jackpot = strip_chars(jackpot, '$,')
    draw_d = datetime.datetime.strptime(draw_date, '%d-%b-%y')
    draw_c = draw_d.strftime('%Y%m%d')
    conn = sqlite3.connect(DB_CONN)
    exec_str = """insert into draws
                        (draw_no,
                        ball_1,
                        ball_2,
                        ball_3,
                        ball_4,
                        ball_5,
                        power_ball,
                        draw_date,
                        draw_jackpot,
                        draw_winners)
                    values ({}, {}, {}, {}, {}, {}, {}, {}, {}, {})""".format(draw_number,
                                                                              winning_numbers[0],
                                                                              winning_numbers[1],
                                                                              winning_numbers[2],
                                                                              winning_numbers[3],
                                                                              winning_numbers[4],
                                                                              winning_numbers[5].replace('P', ''),
                                                                              draw_c,
                                                                              plain_jackpot,  # jackpot,
                                                                              no_of_winners)
    #  print(exec_str)
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
    return input('Enter your numbers: ').upper().split(' ')


if __name__ == '__main__':
    main()
