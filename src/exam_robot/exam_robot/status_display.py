#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String

class StatusDisplayNode(Node):
    def __init__(self):
        super().__init__('status_display_node')
        
        # --- Переменные для хранения последних полученных данных ---
        self.battery_level = 100.0  # Значение по умолчанию
        self.distance = 3.0          # Значение по умолчанию
        
        # --- Флаги получения данных (для отладки) ---
        self.received_battery = False
        self.received_distance = False
        
        # --- Предыдущий статус для отслеживания изменений ---
        self.previous_status = ""
        
        # --- Подписки ---
        # Подписка на топик батареи
        self.battery_sub = self.create_subscription(
            Float32,
            '/battery_level',
            self.battery_callback,
            10)
        
        # Подписка на топик расстояния
        self.distance_sub = self.create_subscription(
            Float32,
            '/distance',
            self.distance_callback,
            10)
        
        # --- Публикация ---
        # Издатель для статуса робота
        self.status_pub = self.create_publisher(String, '/robot_status', 10)
        
        # --- Таймер для периодической публикации (2 Hz) ---
        self.timer = self.create_timer(0.5, self.timer_callback)  # 0.5 сек = 2 Hz
        
        self.get_logger().info('Status Display Node запущен. Ожидание данных...')

    def battery_callback(self, msg):
        """Обновляет текущий уровень батареи"""
        self.battery_level = msg.data
        if not self.received_battery:
            self.received_battery = True
            self.get_logger().info(f'Получены первые данные батареи: {self.battery_level:.1f}%')
        
        # Для отладки можно логировать каждое полученное значение (с ограничением)
        self.get_logger().debug(f'Battery updated: {self.battery_level:.1f}%')

    def distance_callback(self, msg):
        """Обновляет текущее расстояние до препятствия"""
        self.distance = msg.data
        if not self.received_distance:
            self.received_distance = True
            self.get_logger().info(f'Получены первые данные расстояния: {self.distance:.2f}м')
        
        self.get_logger().debug(f'Distance updated: {self.distance:.2f}м')

    def determine_status(self):
        """
        Определяет статус робота на основе текущих значений
        батареи и расстояния согласно заданной логике.
        """
        battery = self.battery_level
        distance = self.distance
        
        # Приоритетная проверка: CRITICAL (самый высокий приоритет)
        if battery < 10.0 or distance < 0.7:
            return "CRITICAL"
        
        # Проверка WARNING: Low battery
        if battery < 20.0:
            return "WARNING: Low battery"
        
        # Проверка WARNING: Obstacle close
        if distance < 1.0:
            return "WARNING: Obstacle close"
        
        # Если все проверки пройдены - ALL OK
        if battery >= 20.0 and distance >= 1.0:
            return "ALL OK"
        
        # Защита от неопределенного состояния (не должно достигаться)
        return "UNKNOWN STATE"

    def timer_callback(self):
        """
        Периодически (2 Hz) публикует статус робота.
        Логирует только при изменении статуса.
        """
        # Проверяем, получены ли данные от обоих датчиков
        if not (self.received_battery and self.received_distance):
            self.get_logger().warn(
                'Ожидание данных от датчиков... '
                f'Battery: {"OK" if self.received_battery else "NO"}, '
                f'Distance: {"OK" if self.received_distance else "NO"}',
                throttle_duration_sec=5.0
            )
            # Не публикуем статус, пока не получим все данные
            return
        
        # Определяем текущий статус
        current_status = self.determine_status()
        
        # Создаем и публикуем сообщение
        status_msg = String()
        status_msg.data = current_status
        self.status_pub.publish(status_msg)
        
        # Логируем только при изменении статуса
        if current_status != self.previous_status:
            log_message = f'Статус изменился: "{self.previous_status}" -> "{current_status}"'
            
            # Используем разные уровни логирования для разных статусов
            if current_status == "CRITICAL":
                self.get_logger().error(log_message + " (КРИТИЧЕСКАЯ СИТУАЦИЯ!)")
            elif "WARNING" in current_status:
                self.get_logger().warn(log_message)
            else:
                self.get_logger().info(log_message)
            
            # Дополнительная информация о показаниях датчиков при изменении
            self.get_logger().info(f'  Показания: Батарея={self.battery_level:.1f}%, Расстояние={self.distance:.2f}м')
            
            self.previous_status = current_status

def main(args=None):
    rclpy.init(args=args)
    node = StatusDisplayNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()