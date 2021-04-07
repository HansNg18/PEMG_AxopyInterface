# PEMG_AxopyInterface

In this application, we train the users to use direct control and abstract control through the myoelectric computer interface (MCI) and evaluate their performance in box and blocks tests and pick and place tests.



## Guildlines
1. System calibration (comfortable contraction level and rest level): 
```python
python PEMG_robolimb_control_v4.py –-Calibration
```
2. System calibration (rest level only): 
```python
python PEMG_robolimb_control_v4.py –-CalibrationLow
```
3.Visualize the EMG signals and MAVs:
```python
python PEMG_robolimb_control_v4.py --Validation
```
4.Record the calibration values:
```python
python PEMG_robolimb_control_v4.py --ReadCalibration
```
5.Change the control algorithm to abstract control:
```python
python PEMG_robolimb_control_v3.py --SetACtrl
```
6.Change the control algorithm to direct control:
```python
python PEMG_robolimb_control_v3.py --SetDCtrl
```
7.MCI training for abstract control with visual feedback:
```python
python PEMG_robolimb_control_v4.py --ACtrainVisible
```
8.MCI training for abstract control without visual feedback:
```python
python PEMG_robolimb_control_v4.py --ACtrainInv
```
9.MCI trials for abstract control with visual feedback:
```python
python PEMG_robolimb_control_v4.py --ACtestVisible
```
10.MCI trials for abstract control without visual feedback:
```python
python PEMG_robolimb_control_v4.py --ACtestInv
```
11.Box and blocks tests for abstract control:
```python
python PEMG_robolimb_control_v4.py --ACBNB
```
12.Pick and place trainings for abstract control:
```python
python PEMG_robolimb_control_v4.py --ACPNPTrain
```
13.Pick and place tests task 1 for abstract control :
```python
python PEMG_robolimb_control_v4.py --ACPNP1
```
14.Pick and place tests task 2 for abstract control :
```python
python PEMG_robolimb_control_v4.py --ACPNP2
```
15.MCI training for direct control with visual feedback:
```python
python PEMG_robolimb_control_v3.py --DCtrainVisible
```
16.MCI training for direct control without visual feedback:
```python
python PEMG_robolimb_control_v3.py --DCtrainInv
```
17.MCI trials for direct control with visual feedback:
```python
python PEMG_robolimb_control_v3.py --DCtestVisible
```
18.MCI trials for direct control without visual feedback:
```python
python PEMG_robolimb_control_v3.py --DCtestInv
```
19.Box and blocks tests for direct control:
```python
python PEMG_robolimb_control_v3.py --DCBNB
```
20.Pick and place trainings for direct control :
```python
python PEMG_robolimb_control_v4.py --DCPNPTrain
```
21.Pick and place tests task 1 for direct control :
```python
python PEMG_robolimb_control_v4.py --DCPNP1
```
22.Pick and place tests task 2 for direct control :
```python
python PEMG_robolimb_control_v4.py --DCPNP2
```



