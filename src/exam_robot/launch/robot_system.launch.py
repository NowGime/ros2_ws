#!/usr/bin/env python3
# launch/robot_system.launch.py

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Запускает всю систему робота:
    - Все пользовательские узлы (battery, distance_sensor, status_display, robot_controller)
    - robot_state_publisher для публикации URDF модели
    """
    
    # ==================== ПУТИ К ФАЙЛАМ ====================
    # Получаем путь к директории share нашего пакета
    pkg_share = get_package_share_directory('exam_robot')
    
    # Путь к URDF файлу относительно корня пакета
    # В собранном пакете файлы из urdf/ копируются в share/pkg/urdf/
    urdf_file = os.path.join(pkg_share, 'urdf', 'exam_robot.urdf')
    
    # Проверяем существование файла (для отладки)
    if not os.path.exists(urdf_file):
        raise FileNotFoundError(f"URDF файл не найден: {urdf_file}")
    
    # ==================== ЧТЕНИЕ URDF ====================
    # Читаем содержимое URDF файла для параметра robot_description
    with open(urdf_file, 'r') as file:
        robot_description_content = file.read()
    
    # ==================== УЗЛЫ ====================
    
    # 1. Узел батареи (1 Hz, публикует /battery_level)
    battery_node = Node(
        package='exam_robot',
        executable='battery_node',
        name='battery_node',
        output='screen',  # Логи в консоль
        parameters=[],    # Можно добавить параметры позже
        arguments=[]      # Аргументы командной строки
    )
    
    # 2. Узел датчика расстояния (5 Hz, публикует /distance)
    distance_sensor_node = Node(
        package='exam_robot',
        executable='distance_sensor',
        name='distance_sensor',
        output='screen',
        # Можно задать начальные параметры через параметры узла
        parameters=[{
            'initial_distance': 3.0,
            'min_distance': 0.5,
            'max_distance': 3.0,
            'step_size': 0.2
        }]
    )
    
    # 3. Узел отображения статуса (2 Hz, публикует /robot_status)
    status_display_node = Node(
        package='exam_robot',
        executable='status_display',
        name='status_display',
        output='screen',
        parameters=[{
            'battery_warning_threshold': 20.0,
            'battery_critical_threshold': 10.0,
            'distance_warning_threshold': 1.0,
            'distance_critical_threshold': 0.7
        }]
    )
    
    # 4. Узел управления роботом (10 Hz, публикует /cmd_vel)
    robot_controller_node = Node(
        package='exam_robot',
        executable='robot_controller',
        name='robot_controller',
        output='screen',
        parameters=[{
            'speed_normal': 0.3,
            'speed_slow': 0.1,
            'turn_rate': 0.5
        }]
    )
    
    # 5. robot_state_publisher - публикует состояние робота в /tf и /robot_description
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content  # Передаем содержимое URDF
        }]
    )
    
    # ==================== ОПЦИОНАЛЬНО: Joint State Publisher для тестирования ====================
    # Этот узел не обязателен, но полезен для тестирования модели без реальных датчиков
    # Он публикует фиктивные состояния суставов для robot_state_publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'source_list': ['']  # Можно подключить к реальным датчикам колес
        }]
    )
    
    # ==================== ОПИСАНИЕ ЗАПУСКА ====================
    return LaunchDescription([
        # Можно добавить аргументы запуска для гибкости
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Использовать симуляционное время'
        ),
        DeclareLaunchArgument(
            'log_level',
            default_value='info',
            description='Уровень логирования (debug/info/warn/error)'
        ),
        
        # Запускаем все узлы
        battery_node,
        distance_sensor_node,
        status_display_node,
        robot_controller_node,
        robot_state_publisher_node,
        
        # Опционально: joint_state_publisher (можно закомментировать при ненадобности)
        # joint_state_publisher_node,
    ])


# Если нужно больше контроля над логированием, можно добавить конфигурацию:
def get_logging_config():
    """Возвращает конфигурацию логирования для всех узлов"""
    return {
        'battery_node': 'info',
        'distance_sensor': 'info',
        'status_display': 'info',
        'robot_controller': 'info',
        'robot_state_publisher': 'warn'  # Меньше логов от стандартного узла
    }