#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist

class DistanceSensorNode(Node):
    def __init__(self):
        super().__init__('distance_sensor_node')
        
        # --- Публикация ---
        # Создаем издателя для топика /distance с частотой 5 Hz
        self.publisher_ = self.create_publisher(Float32, '/distance', 10)
        
        # --- Подписка ---
        # Подписываемся на команды скорости, чтобы знать, движется ли робот
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
        
        # --- Переменные состояния ---
        # Текущее измеренное расстояние (начинаем с 3.0 метров)
        self.current_distance = 3.0
        
        # Направление движения: 0 - стоим, 1 - вперед, -1 - назад
        self.motion_direction = 0
        
        # Скорость изменения расстояния в зависимости от направления
        self.distance_step = 0.2  # метры за 0.2 секунды
        
        # Таймер для публикации с частотой 5 Hz (каждые 0.2 секунды)
        self.timer = self.create_timer(0.2, self.timer_callback)
        
        self.get_logger().info('Distance Sensor Node запущен. Distance: 3.0м')

    def cmd_vel_callback(self, msg):
        """
        Обработчик команд скорости.
        Определяем направление движения на основе linear.x
        """
        linear_x = msg.linear.x
        
        # Определяем направление движения с допуском на погрешность
        if abs(linear_x) < 0.01:  # Стоим (учитываем погрешность float)
            self.motion_direction = 0
            self.get_logger().debug('Робот стоит', throttle_duration_sec=2.0)
        elif linear_x > 0:  # Движется вперед
            self.motion_direction = 1
            self.get_logger().debug('Робот едет вперед', throttle_duration_sec=2.0)
        else:  # Движется назад (linear_x < 0)
            self.motion_direction = -1
            self.get_logger().debug('Робот едет назад', throttle_duration_sec=2.0)

    def update_distance(self):
        """
        Обновляет значение distance в зависимости от направления движения.
        Возвращает новое значение расстояния.
        """
        if self.motion_direction == 0:
            # Если стоим - расстояние возвращается к 3.0м (датчик успокаивается)
            # Плавно возвращаем к 3.0 для реалистичности
            if self.current_distance < 3.0:
                self.current_distance = min(3.0, self.current_distance + self.distance_step)
            elif self.current_distance > 3.0:
                self.current_distance = max(3.0, self.current_distance - self.distance_step)
                
        elif self.motion_direction == 1:
            # Движение вперед - приближаемся к препятствию
            self.current_distance -= self.distance_step
            # Минимум: 0.5 метра
            if self.current_distance < 0.5:
                self.current_distance = 0.5
                self.get_logger().warn('Минимальное расстояние достигнуто!', throttle_duration_sec=1.0)
                
        elif self.motion_direction == -1:
            # Движение назад - удаляемся от препятствия
            self.current_distance += self.distance_step
            # Максимум: 3.0 метра
            if self.current_distance > 3.0:
                self.current_distance = 3.0
        
        return self.current_distance

    def timer_callback(self):
        """
        Таймер срабатывает каждые 0.2 секунды (5 Hz).
        Обновляет расстояние и публикует его.
        """
        # Обновляем значение расстояния
        distance_value = self.update_distance()
        
        # Создаем и публикуем сообщение
        msg = Float32()
        msg.data = distance_value
        self.publisher_.publish(msg)
        
        # Логируем для отладки (с ограничением частоты, чтобы не спамить)
        self.get_logger().debug(f'Опубликовано расстояние: {distance_value:.2f}м')

def main(args=None):
    rclpy.init(args=args)
    node = DistanceSensorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()