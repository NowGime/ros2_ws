from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'exam_robot'

setup(
    name=package_name,
    version='0.0.1',  # Лучше указать версию
    packages=find_packages(exclude=['test']),
    
    # ПРАВИЛЬНЫЕ data_files
    data_files=[
        # Файлы ресурсов
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        
        # package.xml
        ('share/' + package_name, ['package.xml']),
        
        # LAUNCH-ФАЙЛЫ (ИСПРАВЛЕНО)
        (os.path.join('share', package_name, 'launch'), 
            glob('launch/*.launch.py')),  # Берем все .launch.py файлы
        
        # URDF ФАЙЛЫ (ДОБАВЛЕНО)
        (os.path.join('share', package_name, 'urdf'), 
            glob('urdf/*.urdf')),
        
        # Конфигурационные файлы (опционально)
        (os.path.join('share', package_name, 'config'), 
            glob('config/*.yaml') if os.path.exists('config') else []),
    ],
    
    install_requires=['setuptools'],
    
    zip_safe=True,
    
    # ЗАПОЛНЕННЫЕ МЕТАДАННЫЕ
    maintainer='student',
    maintainer_email='student@example.com',  # Реальный email
    description='ROS2 package for exam robot with battery, distance sensor, and controller',
    license='Apache License 2.0',
    
    extras_require={
        'test': ['pytest'],
    },
    
    entry_points={
        'console_scripts': [
            'battery_node = exam_robot.battery_node:main',      # Пробел после =
            'distance_sensor = exam_robot.distance_sensor:main',
            'robot_controller = exam_robot.robot_controller:main',
            'status_display = exam_robot.status_display:main',
        ],
    },
)