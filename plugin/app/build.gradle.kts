plugins {
    id("com.android.library")
    id("kotlin-android")
    id("com.github.recloudstream.gradle")
}

cloudstream {
    name = "HyperT"
    label = "HyperT"
    description = "trgoal"
    authors = "HyperTV0"
    version = 1
    language = "tr"
}

android {
    compileSdk = 33
    defaultConfig {
        minSdk = 21
        targetSdk = 33
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = "1.8"
    }
}

dependencies {
    implementation("com.github.recloudstream:cloudstream:pre-release")
    implementation(kotlin("stdlib"))
    implementation("com.github.Blatzar:NiceHttp:0.4.1")
    implementation("org.jsoup:jsoup:1.13.1")
}
