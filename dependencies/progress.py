import sys

__all__ = ["put_progress"]

def put_progress(loop_length, loop_current, message='', resolution=20):
	output = "\r[{}{}] {:0.0%} {}"
	persent = loop_current/loop_length
	pass_count = round(resolution * persent)
	remain_count = round(resolution * (1 - persent)) 
	sys.stdout.write(output.format('#'*pass_count, '.'*remain_count, persent, message))