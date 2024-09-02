import ctypes
import offsets
from ext_types import * 
from memfuncs import memfunc

# Inicialização dos valores da tela (pre-calculados)
user32 = ctypes.WinDLL('user32')
width = user32.GetSystemMetrics(0)
height = user32.GetSystemMetrics(1)
mem = memfunc()
client_dll_base = mem.searchcliente()

# Cálculo de fatores de ajuste da tela (pre-calculados)
width_float = float(width)
height_float = float(height)
half_width = width_float / 2.0
half_height = height_float / 2.0
half = 0.5

def world_to_screen(view_matrix: Matrix, position: Vector3):
    mat = view_matrix.matrix

    x, y, z = position.x, position.y, position.z

    screen_x = (mat[0][0] * x + mat[0][1] * y + mat[0][2] * z + mat[0][3])
    screen_y = (mat[1][0] * x + mat[1][1] * y + mat[1][2] * z + mat[1][3])
    w = (mat[3][0] * x + mat[3][1] * y + mat[3][2] * z + mat[3][3])

    invw = 1.0 / w
    screen_x *= invw
    screen_y *= invw

    x = half_width + half * screen_x * width_float + half
    y = half_height - half * screen_y * height_float + half

    return x, y

def get_entities_info(offsets: Offset, team_check: bool) -> List[Entity]:
    entities = []

    # Lê o ponteiro da lista de entidades
    entity_list = mem.ReadPointer(client_dll_base + offsets.dwEntityList)
    if not entity_list:
        return entities

    # Lê o ponteiro do jogador local e sua posição
    local_player_p = mem.ReadPointer(client_dll_base + offsets.dwLocalPlayerPawn)
    if not local_player_p:
        return entities

    local_player_game_scene = mem.ReadPointer(local_player_p, offsets.m_pGameSceneNode)
    if not local_player_game_scene:
        return entities

    local_player_scene_origin = mem.ReadVec(local_player_game_scene, offsets.m_nodeToWorld)
    view_matrix_flat = mem.ReadMatrix(client_dll_base + offsets.dwViewMatrix)
    view_matrix = Matrix([
        view_matrix_flat[0:4],
        view_matrix_flat[4:8],
        view_matrix_flat[8:12],
        view_matrix_flat[12:16]
    ])

    bones = {
        "head": 6,
        "neck_0": 5,
        "spine_1": 4,
        "spine_2": 2,
        "pelvis": 0,
        "arm_upper_L": 8,
        "arm_lower_L": 9,
        "hand_L": 10,
        "arm_upper_R": 13,
        "arm_lower_R": 14,
        "hand_R": 15,
        "leg_upper_L": 22,
        "leg_lower_L": 23,
        "ankle_L": 24,
        "leg_upper_R": 25,
        "leg_lower_R": 26,
        "ankle_R": 27,
    }

    for i in range(64):
        # Inicializa a entidade temporária
        temp_entity = Entity(
            Health=0,
            Team=0,
            Name="",
            Position=Vector2(0, 0),
            Bones={},
            HeadPos=Vector3(0, 0, 0),
            Distance=0,
            Rect=Rectangle(0, 0, 0, 0)
        )

        # Estrutura para armazenar informações temporárias
        temp_info = {
            "list_entry": None,
            "entity_controller": None,
            "entity_controller_pawn": None,
            "entity_pawn": None,
            "entity_life_state": None,
            "entity_team": None,
            "entity_health": None,
            "entity_name": None,
            "sanitized_name": None,
            "game_scene": None,
            "entity_bone_array": None,
            "entity_origin": None,
            "entity_bones": {}
        }

        # Lê o ponteiro da entrada da lista de entidades
        temp_info["list_entry"] = mem.ReadPointer(entity_list, (8 * (i & 0x7FFF) >> 9) + 16)
        if not temp_info["list_entry"]:
            continue

        # Lê o controlador da entidade
        temp_info["entity_controller"] = mem.ReadPointer(temp_info["list_entry"], 120 * (i & 0x1FF))
        if not temp_info["entity_controller"]:
            continue

        # Lê o pawn da entidade e verifica se é válido
        temp_info["entity_controller_pawn"] = mem.ReadPointer(temp_info["entity_controller"], offsets.m_hPlayerPawn)
        if not temp_info["entity_controller_pawn"]:
            continue

        temp_info["list_entry"] = mem.ReadPointer(entity_list, (0x8 * ((temp_info["entity_controller_pawn"] & 0x7FFF) >> 9) + 16))
        if not temp_info["list_entry"]:
            continue

        temp_info["entity_pawn"] = mem.ReadPointer(temp_info["list_entry"], 120 * (temp_info["entity_controller_pawn"] & 0x1FF))
        if not temp_info["entity_pawn"] or temp_info["entity_pawn"] == local_player_p:
            continue

        # Verifica o estado da vida da entidade
        temp_info["entity_life_state"] = mem.ReadInt(temp_info["entity_pawn"], offsets.m_lifeState)
        if temp_info["entity_life_state"] != 256:
            continue

        # Verifica a equipe da entidade e se necessário, verifica se é do mesmo time que o jogador local
        temp_info["entity_team"] = mem.ReadInt(temp_info["entity_pawn"], offsets.m_iTeamNum)
        if temp_info["entity_team"] == 0 or (team_check and mem.ReadInt(local_player_p, offsets.m_iTeamNum) == temp_info["entity_team"]):
            continue

        # Verifica a saúde da entidade
        temp_info["entity_health"] = mem.ReadInt(temp_info["entity_pawn"], offsets.m_iHealth)
        if temp_info["entity_health"] < 1 or temp_info["entity_health"] > 100:
            continue

        # Lê e sanitiza o nome da entidade
        entity_name_address = mem.ReadPointer(temp_info["entity_controller"], offsets.m_sSanitizedPlayerName)
        if not entity_name_address:
            continue

        temp_info["entity_name"] = mem.ReadString(entity_name_address, 64)
        if not temp_info["entity_name"]:
            continue

        temp_info["sanitized_name"] = ''.join(c for c in temp_info["entity_name"] if c.isalnum() or c in ' .,!')

        # Lê o nó de cena do jogo e a matriz de ossos
        temp_info["game_scene"] = mem.ReadPointer(temp_info["entity_pawn"], offsets.m_pGameSceneNode)
        if not temp_info["game_scene"]:
            continue

        temp_info["entity_bone_array"] = mem.ReadPointer(temp_info["game_scene"], offsets.m_modelState + offsets.m_boneArray)
        if not temp_info["entity_bone_array"]:
            continue

        # Lê a origem da entidade
        temp_info["entity_origin"] = mem.ReadVec(temp_info["entity_pawn"], offsets.m_vOldOrigin)
        if not temp_info["entity_origin"]:
            continue

        # Processa os ossos da entidade
        for bone_name, bone_index in bones.items():
            current_bone = mem.ReadVec(temp_info["entity_bone_array"], bone_index * 32)
            if bone_name == "head":
                entity_head = current_bone

            bone_x, bone_y = world_to_screen(view_matrix, current_bone)
            temp_info["entity_bones"][bone_name] = Vector2(bone_x, bone_y)

        # Calcula a posição da cabeça e o retângulo da entidade na tela
        entity_head_top = Vector3(entity_head.x, entity_head.y, entity_head.z + 7)
        entity_head_bottom = Vector3(entity_head.x, entity_head.y, entity_head.z - 5)
        screen_pos_head_x, screen_pos_head_top_y = world_to_screen(view_matrix, entity_head_top)
        _, screen_pos_head_bottom_y = world_to_screen(view_matrix, entity_head_bottom)
        screen_pos_feet_x, screen_pos_feet_y = world_to_screen(view_matrix, temp_info["entity_origin"])
        entity_box_top = Vector3(temp_info["entity_origin"].x, temp_info["entity_origin"].y, temp_info["entity_origin"].z + 70)
        _, screen_pos_box_top = world_to_screen(view_matrix, entity_box_top)

        # Calcula a altura da caixa da entidade
        box_height = screen_pos_feet_y - screen_pos_box_top

        # Preenche as informações da entidade e adiciona à lista
        temp_entity.Health = temp_info["entity_health"]
        temp_entity.Team = temp_info["entity_team"]
        temp_entity.Name = temp_info["sanitized_name"]
        temp_entity.Distance = distance_vec3(temp_info["entity_origin"], local_player_scene_origin)
        temp_entity.Position = Vector2(screen_pos_feet_x, screen_pos_feet_y)
        temp_entity.Bones = temp_info["entity_bones"]
        temp_entity.HeadPos = Vector3(screen_pos_head_x, screen_pos_head_top_y, screen_pos_head_bottom_y)
        temp_entity.Rect = Rectangle(screen_pos_box_top, screen_pos_feet_x - box_height / 4, screen_pos_feet_x + box_height / 4, screen_pos_feet_y)

        entities.append(temp_entity)

    return entities


def get_offsets() -> Offset:
    offsets_obj = Offset(
        dwViewMatrix = offsets.Client().offset("dwViewMatrix"),
        dwLocalPlayerPawn = offsets.Client().offset("dwLocalPlayerPawn"),
        dwEntityList = offsets.Client().offset("dwEntityList"),
        m_hPlayerPawn = offsets.Client().get("CCSPlayerController", "m_hPlayerPawn"),
        m_iHealth = offsets.Client().get("C_BaseEntity", "m_iHealth"),
        m_lifeState = offsets.Client().get("C_BaseEntity", "m_lifeState"),
        m_iTeamNum = offsets.Client().get("C_BaseEntity", "m_iTeamNum"),
        m_vOldOrigin = offsets.Client().get("C_BasePlayerPawn", "m_vOldOrigin"),
        m_pGameSceneNode = offsets.Client().get("C_BaseEntity", "m_pGameSceneNode"),
        m_modelState = offsets.Client().get("CSkeletonInstance", "m_modelState"),
        m_boneArray = 128,
        m_nodeToWorld = offsets.Client().get("CGameSceneNode", "m_nodeToWorld"),
        m_sSanitizedPlayerName = offsets.Client().get("CCSPlayerController", "m_sSanitizedPlayerName"),
    )

    return offsets_obj
