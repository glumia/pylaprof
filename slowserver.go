package main

import (
	"fmt"
	"log"
	"net/http"
	"time"
)

func main() {
	http.HandleFunc("/", func(rw http.ResponseWriter, req *http.Request) {
		fmt.Println("Serving request! After a nap of 3 seconds...")
		time.Sleep(time.Second * 3)
		rw.WriteHeader(200)
		rw.Write([]byte("ciao :)"))
	})
	log.Fatal(http.ListenAndServe(":8080", nil))
}
