# Part 2 Integration Test Design

## System Summary

StreetRace Manager is implemented as a command-line system with the required
modules:

- Registration
- Crew Management
- Inventory
- Race Management
- Results
- Mission Planning

It also includes two additional relevant modules:

- Scheduling
- Maintenance

The integration tests focus on how data moves between these modules instead of
testing each function in isolation.

## Test Execution Summary

Test date: March 21, 2026

Commands used:

```bash
python -m pytest integration/tests/test_integration_flows.py
python -m pytest integration/tests
```

Observed results:

- `integration/tests/test_integration_flows.py`: `15 passed`
- `integration/tests`: `69 passed`

Main file for the cross-module scenarios:

- `integration/tests/test_integration_flows.py`

## Integration Test Cases

### IT-01 Register a Driver and Enter the Driver Into a Race

- Scenario: Register `Mia` as a driver, add a car, create a race, and enter the race.
- Modules involved: Registration, Inventory, Race Management, Scheduling
- Why this test is needed: It checks the most basic real workflow of the system. If this flow fails, the race system cannot be used at all.
- Expected result: The driver should be accepted into the race and linked to the chosen car.
- Actual result after testing: Passed. `Mia` was entered into `neon-nights` with `Velocity`.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_register_driver_then_enter_the_driver_into_a_race`

### IT-02 Assign Driver Role After Registration and Then Enter a Race

- Scenario: Register `Mia` as a mechanic first, then assign the driver role through Crew Management before entering a race.
- Modules involved: Registration, Crew Management, Inventory, Race Management, Scheduling
- Why this test is needed: It proves that role changes made in one module are correctly respected by another module later.
- Expected result: After the driver role is assigned, the crew member should be allowed to enter the race.
- Actual result after testing: Passed. The role update was respected and the race entry succeeded.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_assigning_driver_role_after_registration_unlocks_race_entry`

### IT-03 Attempt to Enter a Race Without a Registered Driver

- Scenario: Create a race and car, but try to enter a crew member who was never registered.
- Modules involved: Registration, Inventory, Race Management
- Why this test is needed: It verifies the business rule that registration must happen before race participation.
- Expected result: Race entry should fail with a clear registration error.
- Actual result after testing: Passed. The system rejected the race entry and reported that the crew member was not registered.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_attempting_to_enter_a_race_without_a_registered_driver_fails`

### IT-04 Complete a Race and Update Results and Cash

- Scenario: Create an active race, complete it, and check rankings and cash.
- Modules involved: Registration, Inventory, Race Management, Results
- Why this test is needed: This is the core business outcome of racing. The system must award points and prize money correctly.
- Expected result: The winner should receive ranking points and the Inventory cash balance should increase by the prize money.
- Actual result after testing: Passed. `Mia` received `5` points and the cash balance increased by `1200`.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_completing_a_race_updates_results_and_inventory_cash`

### IT-05 Block a Same-Slot Mission When the Car Is Already Reserved for a Race

- Scenario: Reserve `Velocity` in a race and then try to use the same car in a delivery mission at the same slot.
- Modules involved: Registration, Inventory, Race Management, Mission Planning, Scheduling
- Why this test is needed: It validates that scheduling conflicts are enforced across different modules, not only inside one module.
- Expected result: The mission should fail because the car is already reserved in the race.
- Actual result after testing: Passed. The system rejected the mission with a scheduling conflict for the car.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_race_reservation_blocks_same_slot_delivery_with_the_same_car`

### IT-06 Block a Same-Slot Race Entry When the Driver Is Already Busy on a Mission

- Scenario: Assign `Mia` to a mission and then try to enter the same person into a race at the same slot.
- Modules involved: Registration, Mission Planning, Inventory, Race Management, Scheduling
- Why this test is needed: It confirms that crew availability is shared correctly across different parts of the system.
- Expected result: The race entry should fail because the driver is already booked for the mission.
- Actual result after testing: Passed. The race entry was rejected with a scheduling conflict for the crew member.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_active_mission_blocks_same_slot_race_entry_for_the_busy_driver`

### IT-07 Fail Cleanly if a Race Loses Its Schedule Link

- Scenario: Create a race, remove its schedule entry, and then try to enter the race.
- Modules involved: Race Management, Scheduling
- Why this test is needed: It checks robustness at a module boundary. Race logic depends on Scheduling, so failures there should produce a proper domain error instead of a crash.
- Expected result: The race flow should stop with a clear StreetRace error.
- Actual result after testing: Passed. The flow now reports that the race is missing its schedule entry.
- Errors or logical issues found: A logical issue was found during testing. Earlier, the system could raise a raw `KeyError` or allow race actions without a schedule link. This was fixed in `L Error 2, Part 2: guard race operations with schedule checks`.
- Automated test: `test_race_workflows_fail_cleanly_if_the_schedule_entry_is_missing`

### IT-08 Damaged Car Flow Requires a Mechanic Before Repair Planning Proceeds

- Scenario: Complete a race with damage, then try to assess the damage before and after registering a mechanic.
- Modules involved: Registration, Inventory, Race Management, Results, Maintenance, Mission Planning
- Why this test is needed: This checks an important business rule from the assignment brief: damaged-car follow-up work must verify mechanic availability.
- Expected result: Repair planning should fail without a mechanic and succeed after a mechanic is registered.
- Actual result after testing: Passed. The first repair attempt failed, and the second succeeded after `Nova` was registered as a mechanic.
- Errors or logical issues found: None in this scenario after the current fixes.
- Automated test: `test_damaged_car_flow_requires_a_mechanic_before_repair_mission_proceeds`

### IT-09 Complete a Race, Auto-Schedule a Repair, and Update Inventory Resources

- Scenario: Finish a damaged race, auto-schedule the repair, start the repair mission, and complete it.
- Modules involved: Registration, Inventory, Race Management, Results, Mission Planning, Maintenance
- Why this test is needed: It validates the full damaged-race to repair pipeline, including money, parts, and final car state.
- Expected result: Prize money should be added, repair labor should be deducted, spare parts should be consumed, and the car should become ready again.
- Actual result after testing: Passed. Cash moved from `1000` to `2000`, one belt was consumed, and the car returned to `ready`.
- Errors or logical issues found: None in this scenario after the current fixes.
- Automated test: `test_completed_race_and_repair_flow_updates_inventory_resources`

### IT-10 Roll Back Race Results if Auto-Repair Planning Fails

- Scenario: Complete a race with damage and request automatic repair scheduling when no mechanic is available.
- Modules involved: Registration, Inventory, Race Management, Results, Maintenance, Mission Planning
- Why this test is needed: It checks transaction-like behavior across modules. If the repair step fails, the race result should not leave half-applied changes behind.
- Expected result: The system should raise an error and leave the race, cash, rankings, car condition, and missions unchanged.
- Actual result after testing: Passed. The race stayed `active`, cash stayed `0`, rankings stayed unchanged, the car stayed `ready`, and no mission was created.
- Errors or logical issues found: A real logical issue was found here. Earlier, the race could become `completed`, prize money could be added, and the car could become `damaged` even though repair planning failed. This was fixed in `L Error 3, Part 2: roll back partial race result updates`.
- Automated test: `test_failed_auto_repair_planning_rolls_back_the_race_result`

### IT-11 Reuse a Repaired Car in a Later Delivery Mission

- Scenario: Finish a race, repair the damaged car, then use the repaired car in a later delivery mission and complete that mission.
- Modules involved: Registration, Inventory, Race Management, Results, Maintenance, Mission Planning, Scheduling
- Why this test is needed: It verifies that one workflow leaves the system in a correct state for the next workflow.
- Expected result: After the repair, the car should be reusable, the mission should complete successfully, and the reward should increase the cash balance.
- Actual result after testing: Passed. The later mission completed and the cash balance ended at `2500`.
- Errors or logical issues found: None in this scenario after the current fixes.
- Automated test: `test_repaired_car_can_complete_a_later_delivery_mission_for_extra_reward`

### IT-12 Reject a Mission When Required Roles Are Unavailable

- Scenario: Plan one mission using the only driver and then try to plan another mission in the same slot with the same required role.
- Modules involved: Registration, Mission Planning, Crew Management, Scheduling
- Why this test is needed: It checks that role availability is enforced before the mission starts, not only after planning.
- Expected result: The second mission should fail because the required driver is already unavailable.
- Actual result after testing: Passed. The second mission was rejected with a missing-availability error.
- Errors or logical issues found: None in this scenario after testing.
- Automated test: `test_missions_cannot_start_if_required_roles_are_unavailable`

### IT-13 Run the Full Demo Flow End to End

- Scenario: Execute the packaged CLI demo from start to finish.
- Modules involved: Registration, Crew Management, Inventory, Race Management, Results, Mission Planning, Scheduling, Maintenance
- Why this test is needed: It gives one final end-to-end check that all main flows can work together in a realistic sequence.
- Expected result: The demo should finish without exceptions and leave the system in a sensible final state.
- Actual result after testing: Passed. The demo completed successfully, the car ended in `ready` state, and the delivery mission was active as designed by the script.
- Errors or logical issues found: None in this scenario after the current fixes.
- Automated test: `test_cli_run_executes_the_demo_flow_end_to_end`

### IT-14 Reject a Duplicate Repair Mission for the Same Damaged Car

- Scenario: Finish a race with damage, create one repair mission for `Velocity`, and then try to schedule a second unfinished repair mission for the same car.
- Modules involved: Registration, Inventory, Race Management, Results, Maintenance, Mission Planning
- Why this test is needed: It checks that the repair workflow does not allow duplicate unfinished jobs for one damaged car. Without this guard, later repair flows can spend parts and cash twice for the same problem.
- Expected result: The second repair mission should be rejected with a clear duplicate-repair error.
- Actual result after testing: Passed. The system blocked the backup repair mission because `Velocity` already had an unfinished repair job.
- Errors or logical issues found: A real logical issue was found here. Earlier, the system allowed overlapping repair missions for the same damaged car, which could later double-charge labor and spare parts. This was fixed in `L Error 4, Part 2: block duplicate repair missions for the same car`.
- Automated test: `test_damaged_car_cannot_receive_a_second_unfinished_repair_mission`

### IT-15 Block a Stale Repair Mission After the Car Was Already Fixed

- Scenario: Plan a repair mission for a damaged car, repair the car before the mission starts, and then try to start the now-stale repair mission.
- Modules involved: Inventory, Maintenance, Mission Planning
- Why this test is needed: It checks that mission start logic still respects the current car state instead of only trusting old mission data.
- Expected result: The repair mission should fail to start because the car is no longer damaged.
- Actual result after testing: Passed. The system rejected the stale repair mission and reported that the car could not start a repair workflow anymore.
- Errors or logical issues found: This scenario was tied to the same repair-state bug. The start flow now revalidates that a repair target is still damaged before activation.
- Automated test: `test_repair_mission_cannot_start_after_the_car_was_already_fixed`

## Errors Found During Part 2 Testing

The main StreetRace issues detected during Part 2 testing were:

- `L Error 1, Part 2: harden the StreetRace module rules`
  The initial rule checks across Scheduling, Mission Planning, Race Management, and Results needed tighter validation.
- `L Error 2, Part 2: guard race operations with schedule checks`
  Race flows did not fail cleanly when their Scheduling dependency was missing.
- `L Error 3, Part 2: roll back partial race result updates`
  Failed auto-repair planning could leave partially applied race-result state behind.
- `L Error 4, Part 2: block duplicate repair missions for the same car`
  A damaged car could collect overlapping repair missions, which created stale repair workflows and risked double-charging labor and spare parts.

## Simple Conclusion

These integration tests show that the modules do not just work alone. They also
share data correctly across registration, race setup, results, repairs,
missions, scheduling, and cash handling.
