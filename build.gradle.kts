buildscript {
    repositories {
        google()
        mavenCentral()
        // JitPack ekliyoruz çünkü eklenti aracı orada
        maven("https://jitpack.io")
    }
    dependencies {
        // Android ve Kotlin standart araçları (Stabil sürümler)
        classpath("com.android.tools.build:gradle:7.0.4")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.6.10")
        
        // İŞTE ÇÖZÜM BU SATIRDA: Eklenti aracını kütüphane gibi ekliyoruz
        classpath("com.github.recloudstream:gradle:master-SNAPSHOT")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven("https://jitpack.io")
    }
}

task("clean", Delete::class) {
    delete(rootProject.buildDir)
}
