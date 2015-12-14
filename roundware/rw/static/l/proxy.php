<?php

/**
 * Proxy requests to http://siswh.dyndns.org/roundware/ so it can
 * be called as though it were a local resource, avoiding XSS limitations.
 *
 * $Id: proxy.php 1827 2012-09-07 18:06:37Z zburke $
 *
 */
main();

function main()
{
	// RW server URL: staging
	$url = 'localhost:8080/api/1/?';
	// $url = 'http://roundware.dyndns.org/api/1/?';
	// $url = 'http://roundware.exploratorium.org/api/1/?';
	// $url = 'http://roundware.famsf.org/api/1/?';
	// RW server URL: production
	// $url = 'http://aas.si.edu/roundware/?';
	//$url = 'http://localhost/roundware/?';

	// valid operations from http://www.roundware.org/trac/wiki/RoundwareProtocol2
	$operations = array(
			'get_config' => TRUE,
			'get_tags' => TRUE,
			'request_stream' => TRUE,
			'modify_stream' => TRUE,
			'move_listener' => TRUE,
			'log_event' => TRUE,
			'heartbeat' => TRUE,
			'create_envelope' => TRUE,
			'add_asset_to_envelope' => TRUE,
			'get_current_streaming_asset' => TRUE,
			'get_asset_info' => TRUE,
			'vote_asset' => TRUE,
			'play_asset_in_stream' => TRUE,
			'skip_ahead' => TRUE,
			'number_of_assets' => TRUE,
			'get_active_users' => TRUE,
			'get_available_assets' => TRUE
			);

	// operation is required
	if (! (isset($_GET['operation']) && isset($operations[$_GET['operation']])) )
	{
		exit('operation was missing or invalid');
	}

	// XSS protection: filter all input variables
	$values = array();
	foreach($_GET as $k => $v)
	{
		$values[$k] = filter_var($v, FILTER_SANITIZE_STRING);
	}

	echo do_curl($url, $values);
}



/**
 * Use cURL to call a remote URL and return the result.
 *
 * @param int $id PK of the project
 * @param array $values hash of key-value pairs, passed as args to the remote server
 *
 * @return string JSON
 */
function do_curl($url, $values)
{
	$curl = curl_init();
	$request = $url . rw_build_query($values);

	// push file upload into the POST request
	if (isset($_FILES['file']))
	{
		$_POST['file'] = '@' . $_FILES['file']['tmp_name'];
	}

	curl_setopt($curl, CURLOPT_POSTFIELDS, $_POST);
	curl_setopt($curl, CURLOPT_URL, $request);
	curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);

	$ret = curl_exec($curl);

	// if the request resulted in an error, return just the error message, nothin' else.
	$json = json_decode($ret);
	if (isset($json->error_message))
	{
		$ret = json_encode((object)array('error_message' => $json->error_message));
	}

	return $ret;
}



/**
 * Given an array of key-value pairs, transform it into a string suitable for passing to
 * cURL without performing any URL encoding as the RW server expects values like this:
 * "...&tags=34,35,36,37,38,39,40" not this: "...&tags=34%2C35%2C36%2C37%2C38%2C39%2C40".
 *
 * @param array hash of key-value pairs
 *
 * @return string HTTP request string, NOT url encoded
 */
function rw_build_query($values)
{
	$str = array();
	foreach ($values as $k => $v)
	{
		$str[] = $k . '=' . $v;
	}

	return implode('&', $str);
}
