module example.com/app_engine_go111_data

require (
	example.com/mypkg v0.0.0
	golang.org/x/net v0.0.0-20181201002055-351d144fa1fc // indirect
	google.golang.org/appengine v1.3.0
)

replace example.com/mypkg => ./deps/example.com/mypkg
