pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
        google()
        maven("https://jitpack.io")
    }
    resolutionStrategy {
        eachPlugin {
            if (requested.id.id == "com.github.recloudstream.gradle") {
                useModule("com.github.recloudstream:gradle:master-SNAPSHOT")
            }
        }
    }
}

rootProject.name = "HyperT"
include(":app")
