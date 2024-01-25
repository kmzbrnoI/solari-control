Control HW & SW for Solari di Udine platform table
==================================================

This repository contains data to make platform table from company Solari di
Udine work.

1. [PCB](pcb) replacing original PCB with CPU Intel 8080 in the table.
2. [Firmware](fw) to the main MCU of our new PCB (ATmega328p).
3. [SW](sw) to interact with the table.
4. [Web interface](web) to control the table via web browser.
5. [Integration with hJOP](sw) script to show data from the particular train
   on the track on the table.

## Flap units order

0. Train type
1. Train number 0 (left)
2. Train number 1
3. Train number 2
4. Train number 3
5. Train number 4 (right)
6. Final station 0 (left)
7. Final station 1
8. Final station 10
9. Final station 11
10. Final station 12
11. Final station 13 (right)
12. Direction left
13. Direction right
14. Departure hours
15. Departure minutes tenths
16. Final station 2
17. Final station 3
18. Final station 4
19. Final station 5
20. Final station 6
21. Final station 7
22. Final station 8
23. Final station 9
24. Departure minutes ones
25. Delay

## Author

Jan Horáček
