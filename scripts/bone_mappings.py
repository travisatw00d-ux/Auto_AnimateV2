"""
Shared bone name mappings between AccuRIG and Mixamo.
Used by export_mixamo.py (forward) and rename_mixamo.py (reverse).
"""

# AccuRIG -> Mixamo (for uploading character to Mixamo)
TO_MIXAMO = {
    'RL_BoneRoot': 'Hips',
    'CC_Base_Spine01': 'Spine',
    'CC_Base_Spine02': 'Spine1',
    'CC_Base_NeckTwist01': 'Neck',
    'CC_Base_Head': 'Head',
    'CC_Base_L_Clavicle': 'LeftShoulder',
    'CC_Base_R_Clavicle': 'RightShoulder',
    'CC_Base_L_Upperarm': 'LeftArm',
    'CC_Base_R_Upperarm': 'RightArm',
    'CC_Base_L_Forearm': 'LeftForeArm',
    'CC_Base_R_Forearm': 'RightForeArm',
    'CC_Base_L_Hand': 'LeftHand',
    'CC_Base_R_Hand': 'RightHand',
    'CC_Base_L_Thigh': 'LeftUpLeg',
    'CC_Base_R_Thigh': 'RightUpLeg',
    'CC_Base_L_Calf': 'LeftLeg',
    'CC_Base_R_Calf': 'RightLeg',
    'CC_Base_L_Foot': 'LeftFoot',
    'CC_Base_R_Foot': 'RightFoot',
    'CC_Base_L_ToeBase': 'LeftToeBase',
    'CC_Base_R_ToeBase': 'RightToeBase',
    'CC_Base_L_Thumb1': 'LeftHandThumb1',
    'CC_Base_L_Thumb2': 'LeftHandThumb2',
    'CC_Base_L_Index1': 'LeftHandIndex1',
    'CC_Base_L_Index2': 'LeftHandIndex2',
    'CC_Base_L_Mid1': 'LeftHandMiddle1',
    'CC_Base_L_Mid2': 'LeftHandMiddle2',
    'CC_Base_L_Ring1': 'LeftHandRing1',
    'CC_Base_L_Ring2': 'LeftHandRing2',
    'CC_Base_L_Pinky1': 'LeftHandPinky1',
    'CC_Base_L_Pinky2': 'LeftHandPinky2',
    'CC_Base_R_Thumb1': 'RightHandThumb1',
    'CC_Base_R_Thumb2': 'RightHandThumb2',
    'CC_Base_R_Index1': 'RightHandIndex1',
    'CC_Base_R_Index2': 'RightHandIndex2',
    'CC_Base_R_Mid1': 'RightHandMiddle1',
    'CC_Base_R_Mid2': 'RightHandMiddle2',
    'CC_Base_R_Ring1': 'RightHandRing1',
    'CC_Base_R_Ring2': 'RightHandRing2',
    'CC_Base_R_Pinky1': 'RightHandPinky1',
    'CC_Base_R_Pinky2': 'RightHandPinky2',
}

# Mixamo -> AccuRIG (for downloading animations back)
TO_ACCURIG = {v: k for k, v in TO_MIXAMO.items()}
