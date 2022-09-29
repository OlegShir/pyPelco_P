import serial, time


class Pelco_P:
	'''Кронштейн https://www.proline-rus.ru/catalog/povorotnye-ustrojstva-800/proline-rs315-60940/
	Угол поворота по горизонтали		0-255 град.   ФАКТ 0-230 град
	Скорость поворота по горизонтали	6/12/20 град. в сек.
	Угол поворота по вертикали			0-60 град. ФАКТ 0-50
	Скорость поворота по вертикали		9 град. в сек.
	'''
	def __init__(self, com_port: str, com_speed: int=9600, need_init_position:bool=False) -> None:
		'''
		Pelco-D protocol - https://evileg.com/en/post/207/ , https://www.epiphan.com/userguides/LUMiO12x/Content/UserGuides/PTZ/3-operation/PELCODcommands.htm
		Pelco-P protocol - https://evileg.com/en/post/208/
		'''
		try:
			self.conn_rs_485 = serial.Serial(com_port, com_speed)
		except:
			print('Connection error...')
			return
	 	# основные команды
		self.command_dict = {
			'Left': 'A0 00 00 04 32 00 AF',
			'Right': 'A0 00 00 02 32 00 AF',
			'Up': 'A0 00 00 08 00 09 AF',
			'Down': 'A0 00 00 10 00 09 AF',
			'Stop': 'A0 00 00 00 00 00 AF',
			'Set Preset': 'A0 00 00 03 00 01 AF',          # установка позиций кронштейна
			'Clear Preset': 'A0 00 00 05 00 01 AF',        # очистка позиций кронштейна
			'Call Preset': 'A0 00 00 07 00 01 AF',         # выбор позиций кронштейна
			'Query Tilt Position': 'A0 00 00 53 00 00 AF', # запрос положения по азимуту?			
		}	

		# выставление в начальное положение
		self.init_position_status = False
		self.init_position()	

	def init_position(self) -> None:
		'''Метод класса обеспечивающий выставление платформы в исходное положение'''
		print('Калибровка...')
		self._code('Call Preset')
		time.sleep(10) # ожидание выставление платформы
		self.init_position_status = True
		print('Калибровка завершена')
		self.position = [0,0]

	def chk_summ(self, command: str) -> str:
		'''Метод класса добавляет контрольную сумму в конец команды управления.
		
		Контрольная сумма представляет собой сумму 
		исключающего ИЛИ, т.е. XOR, байтов с 1-го по 7-й.
		'''
		command_array = command.split(' ')		
		summ = 0x00
		for i in command_array:
			summ ^= int(i,16)
		# замена формата 0х00 на 00
		string_summ = format(summ, 'x')
		if len(string_summ) < 2:
			string_summ = f'0{string_summ}'
		
		return f'{command} {string_summ}'

	def set_new_position(self, new_position: list) -> None:
		'''Метод класса обеспечивает перемещение платформы на новою позицию.
		'''
		x1, y1 = new_position
		if x1>125 or x1<-125 or y1>0 or y1<-55:
			print('Значения выходят за предел поворота')
			return
		x0, y0 = self.position
		goto_x = 'None'
		goto_y = 'None'
		if x0 > x1:
			goto_x = 'Left'
		if x0 < x1:
			goto_x = 'Right'
		if goto_x != 'None':
			time_move_x = abs(x0-x1)/12.7
			self._code(goto_x, time_to_move=time_move_x)	
		if y0 > y1:
			goto_y = 'Down'
		if y0 < y1:
			goto_y = 'Up'
		if goto_y != 'None':
			time_move_y = abs(y0-y1)/11
			self._code(goto_y, time_to_move=time_move_y)
		
		self.position = [x1, y1]
		
	def _code(self, command:str, time_to_move: float = 0) -> None:
		# получение команды из словаря
		get_command = self.command_dict.get(command)
		# если команда существует
		if get_command:
			string_command = bytearray.fromhex(self.chk_summ(get_command))
			self.conn_rs_485.write(string_command)
			# если команда связана с движением
			if time_to_move > 0:
				time.sleep(time_to_move)
				self._code('Stop')
		else:
			print('Command not found')
     
	def __del__(self) -> None:
		self.conn_rs_485.close()


if __name__ == '__main__':
	
	pass