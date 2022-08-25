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
dimension = [0, 0]  # width, height
steps = {"N": 0, "E": 1, "W": -1, "S": 0}
# turns = {
#     "N": {"L": "W", "R": "E"},
#     "S": {"L": "E", "R": "W"},
#     "E": {"L": "N", "R": "S"},
#     "W": {"L": "S", "R": "N"},
# }


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

    dimension = data["arena"]["dims"]
    steps.update({"N": dimension[0] * -1, "E": 1, "W": -1, "S": dimension[0]})

    states = data["arena"]["state"]

    my_name = data["_links"]["self"]["href"]
    my_location = get_location(states[my_name]["x"], states[my_name]["y"])
    my_direction = states[my_name]["direction"]
    my_target_spaces = get_target_spaces(my_location, my_direction)

    if not my_target_spaces:
        # TODO: check can move after turn L/R?
        logger.info(
            "Can't Move Forward/Throw! Just turn left or right! my location: {}, my direction: {}".format(
                my_location, my_direction
            )
        )
        return LR_MOVES[random.randrange(len(LR_MOVES))]

    if states[my_name]["wasHit"]:
        # run away!
        logger.info("Lari Maju!")
        return "F"

    logger.info(
        "my location: {}, my direction: {}, my target spaces: {}".format(
            my_location, my_direction, my_target_spaces
        )
    )

    for key in states:
        if key == my_name:
            continue
        location = get_location(states[key]["x"], states[key]["y"])
        if location in my_target_spaces:
            logger.info("Serang!")
            return "T"
        logger.info(
            "{}: x:{},y:{} => loc:{}, dir: {}".format(
                key,
                states[key]["x"],
                states[key]["y"],
                location,
                states[key]["direction"],
            )
        )
    if can_move_forward(my_target_spaces[-1], my_direction):
        # TODO: check if there are targets to move forward
        logger.info("Maju!")
        return "F"
    # TODO: check can move after turn L/R?
    return LR_MOVES[random.randrange(len(LR_MOVES))]


def can_move_forward(location, direction):
    if direction == "N" and location <= dimension[0]:
        return False
    if direction == "S" and location + dimension[0] > dimension[0] * dimension[1]:
        return False
    if direction == "W" and location % dimension[0] == 1:
        return False
    if direction == "E" and location % dimension[0] == 0:
        return False
    return True


def get_target_spaces(location, direction):
    target_spaces = []
    if can_move_forward(location, direction):
        target_1 = location + steps[direction]
        target_spaces.append(target_1)
        if can_move_forward(target_1, direction):
            target_2 = target_1 + steps[direction]
            target_spaces.append(target_2)
            if can_move_forward(target_2, direction):
                target_3 = target_2 + steps[direction]
                target_spaces.append(target_3)
    return target_spaces


def get_location(x, y):
    return int(dimension[0]) * y + x + 1


def get_target_locations(me):
    pass


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
