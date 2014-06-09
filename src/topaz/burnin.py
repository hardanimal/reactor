#!/usr/bin/env python
# encoding: utf-8
from topaz import fsm
from topaz.config import DEVICE_LIST
from topaz.chamber import Chamber, ChamberStates
from topaz.pwr import PowerSupply


def main():
    ps = PowerSupply()
    setting = {"volt": 12.0, "curr": 15.0, "ovp": 13.0, "ocp": 20.0}

    chamber1 = Chamber(DEVICE_LIST[0], ps, ps_node=5,
                       ps_set=setting, Chamber_id=0)
    chamber2 = Chamber(DEVICE_LIST[1], ps, ps_node=6,
                       ps_set=setting, Chamber_id=1)

    f1 = fsm.StateMachine(chamber1)
    f1.run()
    f2 = fsm.StateMachine(chamber2)
    f2.run()

    f1.en_queue(ChamberStates.INIT)
    f1.en_queue(ChamberStates.WORK)
    f2.en_queue(ChamberStates.INIT)
    f2.en_queue(ChamberStates.WORK)


if __name__ == "__main__":
    main()
