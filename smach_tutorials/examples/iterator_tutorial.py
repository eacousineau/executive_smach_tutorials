#! /usr/bin/env python

import roslib
roslib.load_manifest('smach')
roslib.load_manifest('smach_ros')
import rospy

import smach
from smach import Iterator, StateMachine, CBState
from smach_ros import ConditionState, IntrospectionServer

def construct_sm():
    sm = StateMachine(outcomes = ['succeeded','aborted','preempted'])
    sm.userdata.numbers = range(25, 88, 3)
    sm.userdata.even_numbers = []
    sm.userdata.odd_numbers = []
    with sm:
        tutorial_it = Iterator(outcomes = ['succeeded','preempted','aborted'],
                            input_keys = ['numbers', 'even_numbers', 'odd_numbers'],
                            it = lambda: range(0, len(sm.userdata.numbers)),
                            output_keys = ['even_numbers', 'odd_numbers'],
                            it_label = 'tutorial_index',
                            exhausted_outcome = 'succeeded')
        with tutorial_it:
            container_sm = StateMachine(outcomes = ['succeeded','preempted','aborted','continue'],
                                    input_keys = ['numbers', 'tutorial_index', 'even_numbers', 'odd_numbers'],
                                    output_keys = ['even_numbers', 'odd_numbers'])
            with container_sm:
                StateMachine.add('EVEN_OR_ODD',
                                 ConditionState(cond_cb = lambda ud:ud.numbers[ud.tutorial_index]%2, input_keys=['numbers', 'tutorial_index']),
                                 {'true':'EVEN',
                                  'false':'ODD' })
                @smach.cb_interface(input_keys=['numbers', 'tutorial_index', 'even_numbers'],output_keys=['odd_numbers'], outcomes=['succeeded'])
                def even_cb(ud):
                    ud.even_numbers.append(ud.numbers[ud.tutorial_index])
                    return 'succeeded'
                StateMachine.add('EVEN', CBState(even_cb), {'succeeded':'continue'})

                @smach.cb_interface(input_keys=['numbers', 'tutorial_index', 'odd_numbers'], output_keys=['odd_numbers'], outcomes=['succeeded'])
                def odd_cb(ud):
                    ud.odd_numbers.append(ud.numbers[ud.tutorial_index])
                    return 'succeeded'
                StateMachine.add('ODD', CBState(odd_cb), {'succeeded':'continue'})

            #close container_sm
            Iterator.set_contained_state('CONTAINER_STATE', container_sm, loop_outcomes=['continue'])
        #close the remap_it
        StateMachine.add('TUTORIAL_IT',tutorial_it,
                     {'succeeded':'succeeded',
                      'aborted':'aborted'})
    return sm

def main():
    rospy.init_node("iterator_tutorial")
    sm_iterator = construct_sm()

    # Run state machine introspection server for smach viewer
    intro_server = IntrospectionServer('iterator_tutorial',sm_iterator,'/ITERATOR_TUTORIAL')
    intro_server.start()


    outcome = sm_iterator.execute()

    rospy.spin()
    intro_server.stop()

if __name__ == "__main__":
    main()
