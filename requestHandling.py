import requests
from creds import zdToken, zdEmail
#from utils import initLogger, zendeskAuth
from utils import zendeskAuth



def getResponse(session, url, method, verbose=False, payload=None):
	'''
	Use to handle common ZD error responses.
	Pass verbose=True to print statements
	'''
	import time
	counter, bigCount = 0, 0
	while bigCount < 6:
		try:
			if method == 'get':
				print(url, type(url))
				resp = session.get(url)
			elif method == 'post' and payload is not None:
				resp = session.post(url, payload)
			elif method == 'put' and payload is not None:
				resp = session.put(url, payload)
			else:
				logging.exception('Request type not known.')
			
			if verbose == True:
				logging.info('{} returned status code {}'.format(url, resp.status_code))
			
			if resp.status_code in [200, 201, 204]:
				return resp
			
			# RATE LIMIT
			while resp.status_code == 429 and counter < 3:
				
				if 'Retry-After' in resp.headers:
					
					if verbose == True:
						logging.info('Pausing for Rate Limit w/ Retry-After: {} seconds. Attempt #{}.'.format(\
								resp.headers['Retry-After'], counter))

					time.sleep(int(resp.headers['Retry-After']))
					counter += 1
					break

				else:
					if verbose == True:
						logging.info('Pausing for Rate Limit but no Retry-After so pausing for 20.')
					time.sleep(20)
					counter += 1
					break

			# Eventually stop retrying.
			if resp.status_code == 429 and counter >= 3:
				if verbose == True:
					logging.info('Rate Limited and unable to break out.')
				return None
			
			# Bad request
			if resp.status_code in [400, 422]:
				logging.error('Status code {} returned! Check data format.'.format(resp.status_code))
				
				if verbose == True:
					logging.error('\tHEADERS: ', resp.headers)
					logging.error('\n\tTRUNCATED CONTENT: ', str(resp.content)[:500])
				return None
			
			while resp.status_code == 409 and counter < 3:
				if verbose == True:
					logging.error('Status code 409 returned. Pausing for 10 seconds and trying again.')
				time.sleep(2)
				counter += 1
				break
			
			if resp.status_code == 409 and counter >= 3:
				logging.info('Multiple 409 codes and unable to get response.')				
				if verbose == True:
					print('\tHEADERS: ', resp.headers)
					print('\n\tTRUNCATED CONTENT: ', str(resp.content)[:500])
				return None
			
			# 500s
			while (500 <= resp.status_code <= 599) and counter < 3:
				
				if 'Retry-After' in resp.headers:
					if verbose == True:
						logging.error('Pausing due to 500 error w/ Retry-After: {} seconds. Attempt #{}.'.format(\
								resp.headers['Retry-After'], counter))
					time.sleep(int(resp.headers['Retry-After']))
					counter += 1
					break
				
				else:
					if verbose == True:
						logging.error('Pausing for 500 but no Retry-After so pausing for 10. Attempt #{}'.format(counter))
					time.sleep(10)
					counter += 1
					break
			
			if (500 <= resp.status_code <= 599) and counter >= 3:
				logging.error('Status code {} returned and unable to get valid response. Attempt #{}'.format(resp.status_code, counter))
				if verbose == True:
					logging.error('\tHEADERS: ', resp.headers)
					logging.error('\n\tTRUNCATED CONTENT: ', str(resp.content)[:500])
				return None
		
		except Exception as ex:
			logging.error('ConnectionError: ', ex)
			session = zendeskAuth()
			time.sleep(1)
		bigCount += 1	
	return None


