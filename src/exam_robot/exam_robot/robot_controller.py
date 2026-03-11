#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class RobotControllerNode(Node):
    def __init__(self):
        super().__init__('robot_controller_node')
        
        # --- Переменные состояния ---
        self.current_status = "UNKNOWN"  # Текущий статус робота
        self.previous_status = "UNKNOWN" # Предыдущий статус для отслеживания изменений
        
        # --- Режимы движения (для отладки и логирования) ---
        self.movement_modes = {
            "ALL OK": "движение вперед (0.3 м/с)",
            "WARNING: Low battery": "замедленное движение (0.1 м/с)",
            "WARNING: Obstacle close": "поворот на месте (0.5 рад/с)",
            "CRITICAL": "полная остановка"
        }
        
        # --- Подписка на статус робота ---
        self.status_sub = self.create_subscription(
            String,
            '/robot_status',
            self.status_callback,
            10)
        
        # --- Публикация команд движения ---
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # --- Таймер для периодической публикации команд (10 Hz) ---
        self.timer = self.create_timer(0.1, self.timer_callback)  # 0.1 сек = 10 Hz
        
        self.get_logger().info('Robot Controller Node запущен. Ожидание статуса...')

    def status_callback(self, msg):
        """
        Обработчик полученного статуса робота.
        Сохраняет текущий статус и проверяет, изменился ли он.
        """
        self.current_status = msg.data
        
        # Проверяем, изменился ли статус (для логирования)
        if self.current_status != self.previous_status:
            self.log_status_change()
            self.previous_status = self.current_status
        
        self.get_logger().debug(f'Получен статус: {self.current_status}')

    def log_status_change(self):
        """Логирует изменение статуса с дополнительной информацией"""
        # Определяем режим движения для нового статуса
        movement_desc = self.movement_modes.get(
            self.current_status, 
            "неопределенное поведение"
        )
        
        # Формируем сообщение в зависимости от статуса
        if self.current_status == "CRITICAL":
            self.get_logger().error(
                f'КРИТИЧЕСКИЙ СТАТУС! Режим: {movement_desc}'
            )
        elif "WARNING" in self.current_status:
            self.get_logger().warn(
                f'Предупреждение: {self.current_status}. Режим: {movement_desc}'
            )
        else:
            self.get_logger().info(
                f'Статус изменен на "{self.current_status}". Режим: {movement_desc}'
            )

    def get_twist_command(self):
        """
        Возвращает команду Twist в зависимости от текущего статуса.
        Согласно заданию:
        - "ALL OK": linear.x = 0.3 м/с
        - "WARNING: Low battery": linear.x = 0.1 м/с
        - "WARNING: Obstacle close": angular.z = 0.5 рад/с
        - "CRITICAL": полная остановка
        """
        twist = Twist()
        
        if self.current_status == "ALL OK":
            twist.linear.x = 0.3
            twist.angular.z = 0.0
            
        elif self.current_status == "WARNING: Low battery":
            twist.linear.x = 0.1
            twist.angular.z = 0.0
            
        elif self.current_status == "WARNING: Obstacle close":
            twist.linear.x = 0.0
            twist.angular.z = 0.5  # Поворот против часовой стрелки
            
        elif self.current_status == "CRITICAL":
            # Полная остановка (все нули)
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            
        else:
            # Неизвестный статус - безопасная остановка
            self.get_logger().warn(
                f'Неизвестный статус "{self.current_status}". Выполнена остановка.',
                throttle_duration_sec=5.0
            )
            twist.linear.x = 0.0
            twist.angular.z = 0.0
        
        return twist

    def timer_callback(self):
        """
        Периодически (10 Hz) публикует команду движения
        на основе текущего статуса.
        """
        # Проверяем, получен ли статус
        if self.current_status == "UNKNOWN":
            self.get_logger().warn(
                'Ожидание первого статуса от Status Display...',
                throttle_duration_sec=5.0
            )
            # Публикуем остановку для безопасности
            twist = Twist()  # все нули
            self.cmd_pub.publish(twist)
            return
        
        # Получаем команду для текущего статуса
        twist = self.get_twist_command()
        
        # Публикуем команду
        self.cmd_pub.publish(twist)
        
        # Для отладки (с ограничением частоты)
        self.get_logger().debug(
            f'CMD: linear.x={twist.linear.x:.2f}, angular.z={twist.angular.z:.2f}',
            throttle_duration_sec=1.0
        )

def main(args=None):
    rclpy.init(args=args)
    node = RobotControllerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # При прерывании гарантированно останавливаем робота
        node.get_logger().info('Остановка робота...')
        twist = Twist()  # все нули
        node.cmd_pub.publish(twist)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()