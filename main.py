# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import random
from flask import Flask, request

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)
moves = ["F", "T", "L", "R"]
LR_MOVES = ["L", "R"]
LRF_MOVES = ["L", "R", "F"]
dimension = [0, 0]  # width, height
steps = {"N": 0, "E": 1, "W": -1, "S": 0}
turns = {
    "N": {"L": "W", "R": "E"},
    "S": {"L": "E", "R": "W"},
    "E": {"L": "N", "R": "S"},
    "W": {"L": "S", "R": "N"},
}
player_locations = {}


@app.route("/", methods=["GET"])
def index():
    return "Let the battle begin!"


@app.route("/", methods=["POST"])
def move():
    request.get_data()
    logger.info(request.json)
    data = request.json

    global dimension
    global steps
    global player_locations
    player_locations = {}

    dimension = data["arena"]["dims"]
    steps.update({"N": dimension[0] * -1, "E": 1, "W": -1, "S": dimension[0]})

    my_name = data["_links"]["self"]["href"]
    states = data["arena"]["state"]

    my_direction = states[my_name]["direction"]
    forward_spaces, forward_target_spaces = get_forward_and_target_spaces(
        states[my_name]["x"], states[my_name]["y"], my_direction
    )
    target_in_forward_spaces = []

    left_spaces = get_forward_spaces(
        states[my_name]["x"], states[my_name]["y"], turns[my_direction]["L"]
    )
    target_in_left_spaces = []
    right_spaces = get_forward_spaces(
        states[my_name]["x"], states[my_name]["y"], turns[my_direction]["R"]
    )
    target_in_right_spaces = []

    for key in states:
        if key == my_name:
            continue
        location = get_location(states[key]["x"], states[key]["y"])
        if not states[my_name]["wasHit"]:
            if location in forward_target_spaces:
                logger.info("====> Serang!")
                return "T"
            if location in forward_spaces:
                target_in_forward_spaces.append(location)
            elif location in left_spaces:
                target_in_left_spaces.append(location)
            elif location in right_spaces:
                target_in_right_spaces.append(location)
        player_locations.update({location: states[key]["direction"]})

    my_location = get_location(states[my_name]["x"], states[my_name]["y"])
    if states[my_name]["wasHit"]:
        # run away!
        # TODO: check attack from
        # right now just find empty spaceflak
        if can_move_forward(my_location, my_direction, check_player=True):
            logger.info("====> Lari ke depan!")
            return "F"
        # check turn left and forward
        if can_move_forward(my_location, turns[my_direction]["L"], check_player=True):
            logger.info("====> Lari ke kiri!")
            return "L"
        logger.info("====> Lari ke kanan!")
        return "R"
        # return LR_MOVES[random.randrange(len(LR_MOVES))]

    # my_target_spaces = get_target_spaces(my_location, my_direction)
    # if not my_target_spaces:
    #     # TODO: check can move after turn L/R?
    #     logger.info(
    #         "Can't Move Forward/Throw! Just turn left or right! my location: {}, my direction: {}".format(
    #             my_location, my_direction
    #         )
    #     )
    #     return LR_MOVES[random.randrange(len(LR_MOVES))]

    logger.info(
        "my location: {}, my direction: {}, my forward spaces: {}, my target spaces: {}".format(
            my_location, my_direction, forward_spaces, forward_target_spaces
        )
    )

    # for key in states:
    #     if key == my_name:
    #         continue
    #     location = get_location(states[key]["x"], states[key]["y"])
    #     if location in my_target_spaces:
    #         logger.info("Serang!")
    #         return "T"
    #     logger.info(
    #         "{}: x:{},y:{} => loc:{}, dir: {}".format(
    #             key,
    #             states[key]["x"],
    #             states[key]["y"],
    #             location,
    #             states[key]["direction"],
    #         )
    #     )
    if target_in_forward_spaces:
        logger.info("====> Kejar Target, Maju!")
        return "F"
    if target_in_left_spaces:
        logger.info("====> Kejar Target, Belok Kiri!")
        return "L"
    if target_in_right_spaces:
        logger.info("====> Kejar Target, Belok Kanan!")
        return "R"
    if forward_spaces:
        logger.info("====> Asal Maju!")
        return "F"
    if left_spaces:
        logger.info("====> Asal Belok Kiri!")
        return "L"
    logger.info("====> Asal Belok Kanan!")
    return "R"
    # return LR_MOVES[random.randrange(len(LR_MOVES))]


def can_move_forward(location, direction, check_player=False):
    # check by dimension
    if direction == "N" and location <= dimension[0]:
        return False
    if direction == "S" and location + dimension[0] > dimension[0] * dimension[1]:
        return False
    if direction == "W" and location % dimension[0] == 1:
        return False
    if direction == "E" and location % dimension[0] == 0:
        return False

    # check by other player locations
    if check_player:
        one_step_forward = location + steps[direction]
        if player_locations.get(one_step_forward, None):
            return False
    return True


def get_forward_and_target_spaces(x, y, direction):
    forward_spaces = []
    target_spaces = []
    if direction == "N":
        forward_spaces = [(dimension[0] * t_y + x + 1) for t_y in range(y)]
        target_spaces = forward_spaces[-3:]
    elif direction == "S":
        forward_spaces = [
            (dimension[0] * t_y + x + 1) for t_y in range(y + 1, dimension[1])
        ]
        target_spaces = forward_spaces[:3]
    elif direction == "W":
        forward_spaces = [(dimension[0] * y + t_x + 1) for t_x in range(x)]
        target_spaces = forward_spaces[-3:]
    else:
        forward_spaces = [
            (dimension[0] * y + t_x + 1) for t_x in range(x + 1, dimension[0])
        ]
        target_spaces = forward_spaces[:3]
    return forward_spaces, target_spaces


def get_forward_spaces(x, y, direction):
    forward_spaces = []
    if direction == "N":
        forward_spaces = [(dimension[0] * t_y + x + 1) for t_y in range(y)]
    elif direction == "S":
        forward_spaces = [
            (dimension[0] * t_y + x + 1) for t_y in range(y + 1, dimension[1])
        ]
    elif direction == "W":
        forward_spaces = [(dimension[0] * y + t_x + 1) for t_x in range(x)]
    else:
        forward_spaces = [
            (dimension[0] * y + t_x + 1) for t_x in range(x + 1, dimension[0])
        ]
    return forward_spaces


# def get_target_spaces(location, direction):
#     target_spaces = []
#     if can_move_forward(location, direction):
#         target_1 = location + steps[direction]
#         target_spaces.append(target_1)
#         if can_move_forward(target_1, direction):
#             target_2 = target_1 + steps[direction]
#             target_spaces.append(target_2)
#             if can_move_forward(target_2, direction):
#                 target_3 = target_2 + steps[direction]
#                 target_spaces.append(target_3)
#     return target_spaces


def get_location(x, y):
    return dimension[0] * y + x + 1


def get_target_locations(me):
    pass


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
