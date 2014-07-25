(ns plugins.cljtest.cljplugin)                   ;; Use the full module name here

(defn -get [obj, attr]
    (py/getattr obj attr)                        ;; Until I remember how to do this properly
)

(defn event_callback [self event]
    (.info (-get self "logger") "Event!")        ;; Output that we got the event
)

(defn setup [self]
    (.info (-get self "logger") "Setup method run.")
    (.add_callback (-get self "events")          ;; Get the events manager and add a callback
        "ReactorStarted" self                    ;; We want to add one for the ReactorStarted event
        ((-get self "wrapper") event_callback)   ;; Wrap our function so that we get self
        0                                        ;; Priority is 0
    )
)