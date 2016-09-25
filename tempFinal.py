from cgitb import handler
from math import sin, cos
import sys
import time

import math
from direct.gui.DirectDialog import YesNoDialog
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import*
from direct.showbase.ShowBase import ShowBase

from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

from panda3d.core import AmbientLight, CollisionSphere, CollisionNode, CollisionHandlerQueue, CollisionTraverser, \
    CollisionHandlerEvent, CollisionHandlerPusher, TextNode, TextureStage, Texture
from panda3d.core import DirectionalLight
from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import Point3
from panda3d.core import BitMask32
from panda3d.core import NodePath
from panda3d.core import PandaNode

from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletHelper
from panda3d.bullet import BulletPlaneShape
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletCapsuleShape
from panda3d.bullet import BulletCharacterControllerNode
from panda3d.bullet import BulletHeightfieldShape
from panda3d.bullet import BulletTriangleMesh
from panda3d.bullet import BulletTriangleMeshShape
from panda3d.bullet import BulletSoftBodyNode
from panda3d.bullet import BulletSoftBodyConfig
from panda3d.bullet import ZUp
from panda3d.physics import PhysicsCollisionHandler, ForceNode, LinearVectorForce
from direct.gui.DirectGui import *


# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
                    pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1,1,1,1),
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)

class CharacterController(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.setupLights()

        # Input
        self.accept('escape', self.doExit)
        self.accept('r', self.doReset)
        self.accept('f3', self.toggleDebug)
        self.accept('space', self.doJump)
        self.accept('1', self.level1)
        self.accept('2', self.level2)

        inputState.watchWithModifiers('forward', 'w')
        inputState.watchWithModifiers('reverse', 's')
        inputState.watchWithModifiers('turnLeft', 'a')
        inputState.watchWithModifiers('turnRight', 'd')

        self.title = addTitle("Rescue Ralphie")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(0.90, "[w]: Walk Lack Forward")
        self.inst3 = addInstructions(0.85, "[a]: Rotate Lack Left")
        self.inst4 = addInstructions(0.80, "[s]: Walk Lack Reverse")
        self.inst5 = addInstructions(0.75, "[d]: Rotate Lack Right")
        self.inst6 = addInstructions(0.70, "[space]: Jump")
        self.inst7 = addInstructions(0.60, "[1] : Press 1 for Level1")
        self.inst8 = addInstructions(0.55, "[2]: Press 2 for Level2")

        # set default color to Sky image
        self.loadBackground("models/sky.png")

        # Adding Sound to the Game
        mySound = base.loader.loadSfx("sounds/overworld.mp3")
        mySound.setLoop(True)
        mySound.play()

        self.counter = {"count":0}
        self.countCoins = self.displayCoins(0.12, "Coins")
        #self.radius = 5.0

        # Task
        taskMgr.add(self.update, 'updateWorld')
        # Task to count coins
        taskMgr.add(self.coins, 'score')
        # Task when enemy attacks
        #taskMgr.add(self.attack, 'attack')

        bk_text = "Health"
        textObject = OnscreenText(text = bk_text, pos = (0.70,0.80),
        scale = 0.05,fg=(0,0,0,1),align=TextNode.ACenter,mayChange=1)
        # Create a frame
        frame = DirectFrame(text = "main", scale = 0.01, pos=(-1,0,1))
        # Add button
        self.bar = DirectWaitBar(text = "", scale = 0.25, value = 100, range=100, pos = (.85,-.75,.75))

        # Setup
        self.setup()

        self.isMoving = False
        self.isJumping = False
        self.isEnemyWalking = False
        self.isEnemyWalking2 = False
        self.isEnemyWalking3 = False
        self.isEnemyWalking4 = False

        base.setFrameRateMeter(True)
        base.disableMouse()
        #base.camera.setPos(0, -200, 10)
        base.camera.setPos(0, -200, 20)
        #base.camera.setPos(self.characterNP.getPos())
        base.camera.setHpr(self.characterNP.getHpr())
        base.camera.lookAt(self.characterNP)

        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

        # This command is required for Panda to render particles
        base.enableParticles()
        self.c = self.loader.loadModel("models/coin")
        self.c.setPos(0, 0, 0)
        self.c.setHpr(90, 0, 90)
        self.c.reparentTo(render)
        self.coin_tex = self.loader.loadTexture("models/coin.jpg")
        self.c.setTexture(self.coin_tex,1)
        self.c.setTag("coin", str(1))

        cs = CollisionSphere(2, 10, 8, 1)
        cnodePath = self.c.attachNewNode(CollisionNode('cnode'))
        cnodePath.node().addSolid(cs)
        cnodePath.node().setFromCollideMask(BitMask32(0x10))
        cnodePath.show()

    def level1(self):
        self.characterNP.setPos(0, 0, 15)
        base.camera.setPos(0, -200, 20)
        #base.camera.setPos(self.characterNP.getPos())
        base.camera.setHpr(self.characterNP.getHpr())
        base.camera.lookAt(self.characterNP)

    def level2(self):
        self.characterNP.setPos(0, 1060, 20)

    def incBar(self, arg):
        self.bar['value'] +=	arg

    def doExit(self):
        self.cleanup()
        sys.exit(1)

    def doReset(self):
        self.cleanup()
        self.setup()

    def toggleDebug(self):
        if self.debugNP.isHidden():
            self.debugNP.show()
        else:
            self.debugNP.hide()

    def doJump(self):
        self.character.setMaxJumpHeight(8.0)
        self.character.setJumpSpeed(12.0)
        self.character.doJump()
        jumpSound = base.loader.loadSfx("sounds/jump.mp3")
        jumpSound.play()
        self.actorNP.play("jump")

    def processInput(self, dt):
        speed = Vec3(0, 0, 0)
        omega = 0.0
        force = Vec3(0, 0, 0)

        if inputState.isSet('forward'): force.setY( 30.0)
        if inputState.isSet('reverse'): force.setY(-10.0)
        if inputState.isSet('left'):    force.setX(-5.0)
        if inputState.isSet('right'):   force.setX( 5.0)
        if inputState.isSet('turnLeft'):  omega =  120.0
        if inputState.isSet('turnRight'): omega = -120.0

        if (inputState.isSet('forward')):
            if self.isMoving is False:
                self.actorNP.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.actorNP.stop()
                self.actorNP.pose("idle",5)
                self.isMoving = False

        self.character.setAngularMovement(omega)
        self.character.setLinearMovement(force, True)

################################################################################################################################
################################################################################################################################

    def update(self, task):
        dt = globalClock.getDt()
        self.processInput(dt)
        self.world.doPhysics(dt, 4, 1./240.)

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.
        camvec = self.characterNP.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 50.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-50))
            camdist = 50.0
        if (camdist < 45.0):
            base.camera.setPos(base.camera.getPos() - camvec*(45-camdist))
            camdist = 45.0

        self.gameOver()

        #coin update
        for coin in render.findAllMatches("**/=coin"):
            d = self.characterNP.getPos() - coin.getPos()
            if d.length() < 5:
                coinSound = base.loader.loadSfx("sounds/coins.mp3")
                coinSound.play()
                self.counter["count"] = self.counter.get("count") + 1
                coin.removeNode()

        # Update when enemy comes
        actorPos = self.characterNP.getPos()
        enemyPos = self.charNP.getPos()
        enemyPos2 = self.charNP2.getPos()
        enemyPos3 = self.charNP3.getPos()
        enemyPos4 = self.charNP4.getPos()

        x,  y,  z = enemyPos - actorPos
        x2, y2, z2 = enemyPos2 - actorPos
        x3, y3, z3 = enemyPos3 - actorPos
        x4, y4, z4 = enemyPos4 - actorPos

        dist = self.findDistance(x, y, z)
        dist2 = self.findDistance(x2, y2, z2)
        dist3 = self.findDistance(x3, y3, z3)
        dist4 = self.findDistance(x4, y4, z4)

        #print "distant:", dist
        if( (dist <= 75) or (dist2 <= 75) or (dist3 <= 75) or (dist4 <= 75) ):
            self.attack()
        else:
            self.dontAttack()
            #self.enemyNP.lookAt(self.actorNP)

        if( (dist <= 5) or (dist2 <= 5) or (dist3 <= 5) or (dist4 <= 5) ):
            self.incBar(-0.5)

        #when game finishes
        ralphiePos = self.characterNP5.getPos()
        x5, y5, z5 = ralphiePos - actorPos
        dist5 = self.findDistance(x5, y5, z5)

        if(dist5 <= 50):
            self.ralphieRescued()

        #print "Character Position: ", self.characterNP.getPos().getY()

        self.floater.setPos(self.characterNP.getPos())
        self.floater.setZ(self.characterNP.getZ() + 5.0)
        base.camera.lookAt(self.floater)
        return task.cont

################################################################################################################################
################################################################################################################################

    def ralphieRescued(self):
        self.character5.setMaxJumpHeight(8.0)
        self.character5.setJumpSpeed(12.0)
        self.character5.doJump()
        #jumpSound = base.loader.loadSfx("sounds/jump.mp3")
        #jumpSound.play()
        self.actorNP5.play("jump")

        #add some text
        output = "You won...You're the best in the world!"
        textObject = OnscreenText(text = output, pos = (0,0.5),
        scale = 0.14,fg=(1,0,0,1),align=TextNode.ACenter,mayChange=1)


    def attack(self):
        if (self.isEnemyWalking is False):
            self.beefyPos.finish()
            self.enemyNP.lookAt(self.actorNP)
            self.enemyNP.setH(self.enemyNP.getH()-180)
            self.enemyNP.loop('walk')
            self.isEnemyWalking = True

            enemyPosInterval1 = self.charNP.posInterval(7, Point3(self.characterNP.getPos()),
            startPos=Point3(self.charNP.getPos()))

            self.enemyInt = Sequence(enemyPosInterval1,  name="enemyInt")
            self.enemyInt.loop()

        if (self.isEnemyWalking2 is False):
            self.beefyPos2.finish()
            self.enemyNP2.lookAt(self.actorNP)
            self.enemyNP2.setH(self.enemyNP2.getH()-180)
            self.enemyNP2.loop('walk')
            self.isEnemyWalking2 = True

            enemyPosInterval2 = self.charNP2.posInterval(7, Point3(self.characterNP.getPos()),
            startPos=Point3(self.charNP2.getPos()))

            self.enemyInt2 = Sequence(enemyPosInterval2,  name="enemyInt2")
            self.enemyInt2.loop()

        if (self.isEnemyWalking3 is False):
            self.beefyPos3.finish()
            self.enemyNP3.lookAt(self.actorNP)
            self.enemyNP3.setH(self.enemyNP3.getH()-180)
            self.enemyNP3.loop('walk')
            self.isEnemyWalking3 = True

            enemyPosInterval3 = self.charNP3.posInterval(7, Point3(self.characterNP.getPos()),
            startPos=Point3(self.charNP3.getPos()))

            self.enemyInt3 = Sequence(enemyPosInterval3,  name="enemyInt3")
            self.enemyInt3.loop()

        if (self.isEnemyWalking4 is False):
            self.beefyPos4.finish()
            self.enemyNP4.lookAt(self.actorNP)
            self.enemyNP4.setH(self.enemyNP4.getH()-180)
            self.enemyNP4.loop('walk')
            self.isEnemyWalking4 = True

            enemyPosInterval4 = self.charNP4.posInterval(7, Point3(self.characterNP.getPos()),
            startPos=Point3(self.charNP4.getPos()))

            self.enemyInt4 = Sequence(enemyPosInterval4,  name="enemyInt4")
            self.enemyInt4.loop()

    def dontAttack(self):
        if (self.isEnemyWalking is True):
            #self.enemyNP.pose('idle', 5)
            self.enemyNP.setH(self.charNP.getH() + 90)
            self.enemyNP2.setH(self.charNP2.getH() + 90)
            self.enemyNP3.setH(self.charNP3.getH() + 270)
            self.enemyNP4.setH(self.charNP4.getH() + 270)

            self.enemyInt.finish()
            self.enemyInt2.finish()
            self.enemyInt3.finish()
            self.enemyInt4.finish()

            self.isEnemyWalking  = False
            self.isEnemyWalking2 = False
            self.isEnemyWalking3 = False
            self.isEnemyWalking4 = False

            self.beefyPos.loop()
            self.beefyPos2.loop()
            self.beefyPos3.loop()
            self.beefyPos4.loop()


    # To find the distance between two actors(co-ordinates)
    def findDistance(self, a, b, c):
            X = a*a
            Y = b*b
            Z = c*c
            sum = X + Y + Z
            dist = math.sqrt(sum)
            return dist

    def cleanup(self):
        self.world = None
        self.render.removeNode()

    def setupLights(self):
        # Light
        alight = AmbientLight('ambientLight')
        alight.setColor(Vec4(0.5, 0.5, 0.5, 1))
        alightNP = render.attachNewNode(alight)

        dlight = DirectionalLight('directionalLight')
        dlight.setDirection(Vec3(1, 1, -1))
        dlight.setColor(Vec4(0.7, 0.7, 0.7, 1))
        dlightNP = render.attachNewNode(dlight)

        self.render.clearLight()
        self.render.setLight(alightNP)
        self.render.setLight(dlightNP)

    def createBox(self):
        angle = -15
        x = 5
        y = 1350
        z = 0
        for i in range(4):
            shape = BulletBoxShape(Vec3(5,7.5,5))
            node = BulletRigidBodyNode('Box')
            node.setMass(0)
            node.addShape(shape)
            np = self.render.attachNewNode(node)
            np.setPos(x, y, z)
            np.setR(angle)
            self.world.attachRigidBody(node)
            nodeModel = self.loader.loadModel("models/stone.egg")
            nodeModel.setScale(10, 15, 10)
            nodeModel.setPos(0, 0, -5)
            nodeModel.reparentTo(np)

            angle = angle * -1
            x = x * -1
            y = y + 55

    # Function to add default background image (Sky)
    def loadBackground(self, imagepath):
        from direct.gui.OnscreenImage import OnscreenImage
        self.background = OnscreenImage(parent=render2dp, image= imagepath)
        base.cam2dp.node().getDisplayRegion(0).setSort(-20)


    def gameOver(self):
        gameOverSound = base.loader.loadSfx("sounds/gameover.mp3")
        if(self.characterNP.getZ() <= 3):
            self.incBar(-2)
            #add some text
            output = "Game Over"
            textObject = OnscreenText(text = output, pos = (0,0.5),
            scale = 0.14,fg=(1,0,0,1),align=TextNode.ACenter,mayChange=1)

            #gameOverSound.play()

    def coins(self, task):
        self.countCoins.removeNode()
        self.countCoins = self.displayCoins(0.12, "Coins X "+str(self.counter.get("count")))
        return task.cont

    def displayCoins(self, pos, msg):
        return OnscreenText(text=msg, style=1, fg=(0, 0, 0, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(1, -pos - 0.04), align=TextNode.ALeft)

    def collectableCoins(self, X, Y, Z, x, y, z, a, b, loop):
            # Coins
            for i in range(loop):
                coinModel = self.loader.loadModel('models/smiley')
                coinModel.reparentTo(self.render)
                coinModel.setScale(0.75)
                coinModel.setPos(X, Y, Z)
                coinModel.setTag("coin", str(i))
                coin_tex = self.loader.loadTexture("models/coin.jpg")
                coinModel.setTexture(coin_tex, 1)
                X = X + x
                Y = Y + y
                Z = Z + z

                if (a == 'X'):
                    if ( i%2 == 0 ): X = X + b
                    else : X = X - b
                if (a == 'Y'):
                    if ( i%2 == 0 ): Y = Y + b
                    else : Y = Y - b
                if (a == 'Z'):
                    if ( i%2 == 0 ): Z = Z + b
                    else : Z = Z - b


    """
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    """

    def setup(self):

        # World
        self.debugNP = self.render.attachNewNode(BulletDebugNode('Debug'))
        #self.debugNP.show()

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.world.setDebugNode(self.debugNP.node())

        """
        # BASE Floor
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        floorNP = self.render.attachNewNode(BulletRigidBodyNode('Floor'))
        floorNP.node().addShape(shape)
        floorNP.setPos(0, 0, -100)
        floorNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(floorNP.node())
        floorNP.setColorScale(0,0,0,1)
        ###
        floorModel = self.loader.loadModel("models/environment")
        floorModel.setScale(50, 50, 1)
        floorModel.setPos(0, 0, -100)
        floorModel.reparentTo(self.render)
        """

        directionalLight = DirectionalLight( "directionalLight" )
        directionalLight.setColor( Vec4( 1, 1, 1, 1 ) )
        directionalLight.setDirection(Vec3(0, 0, -1))
        directionalLightNP = render.attachNewNode(directionalLight)


        #######################################################
        #           FLOOR 1
        ########################################################
        shape = BulletBoxShape(Vec3(10,150,1))
        floorNode = BulletRigidBodyNode('Floor1')
        floorNode.addShape(shape)
        floorNodePath = self.render.attachNewNode(floorNode)
        floorNodePath.setCollideMask(BitMask32.allOn())
        floorNodePath.setPos(0, 0, 0)
        self.world.attachRigidBody(floorNodePath.node())
        floorModel = self.loader.loadModel("models/stone.egg")
        floorModel.setScale(20, 300, 1)
        floorModel.setPos(0, 0, 0)
        floorModel.reparentTo(floorNodePath)

        floorModel.setLight(directionalLightNP)

        ts = TextureStage.getDefault()
        texture = floorModel.getTexture()
        floorModel.setTexOffset(ts, 1, 1)
        floorModel.setTexScale(ts, 75, 75)

        floorTexture = self.loader.loadTexture("layingrock-c.jpg")#wood.png")
        floorModel.setTexture(floorTexture, 1)
        #floorTexture.setWrapU(Texture.WMRepeat)
        #floorTexture.setWrapV(Texture.WMRepeat)

 	    # normal-map texture for the plane
        self.normal = self.loader.loadTexture('coin-texture.jpg')#layingrock-n.jpg')
        self.ts = TextureStage('ts')
	self.ts.setMode(TextureStage.MNormal)

        floorModel.setTexture(self.ts, self.normal)
        floorModel.setShaderAuto()

        # Coins
        X, Y, Z = floorNodePath.getPos()
        Y = Y + 50
        Z = Z + 12
        self.collectableCoins(X, Y, Z, 0, 12, 0, 'Z', 2, 3)

        ####################
        # FLOOR STEPS - 1
        ###################
        y = 190
        z = 1
        x = 0
        for i in range(3):
            shape = BulletBoxShape(Vec3(5, 7.5, 1))
            floorNode = BulletRigidBodyNode('Floor')
            floorNode.setMass(0)
            floorNode.addShape(shape)
            floorNodePath = self.render.attachNewNode(floorNode)
            floorNodePath.setCollideMask(BitMask32.allOn())
            floorNodePath.setPos(x, y, z)
            self.world.attachRigidBody(floorNodePath.node())
            floorModel = self.loader.loadModel("models/stone.egg")
            floorModel.setScale(10, 15, 1)
            floorModel.setPos(0, 0, 0)
            floorModel.reparentTo(floorNodePath)

            floorModel.setTexture(floorTexture, 1)

            X, Y, Z = floorNodePath.getPos()

            if (i == 0) :
                PosInterval1 = floorNodePath.posInterval(7, Point3(X + 5, Y, Z),
                startPos=Point3(X - 5, Y, Z))
                PosInterval2 = floorNodePath.posInterval(7, Point3(X - 5, Y, Z),
                startPos=Point3(X + 5, Y, Z))

                self.movinStairs1 = Sequence(PosInterval1, PosInterval2, name="movinStairs1")
                self.movinStairs1.loop()
            if (i == 1) :
                PosInterval12 = floorNodePath.posInterval(7, Point3(floorNodePath.getPos()),
                startPos=Point3(X + 5, Y, Z))
                PosInterval22 = floorNodePath.posInterval(7, Point3(X + 5, Y, Z),
                startPos=Point3(X - 5, Y, Z))

                self.movinStairs2 = Sequence(PosInterval12, PosInterval22, name="movinStairs2")
                self.movinStairs2.loop()
            if (i == 2) :
                PosInterval13 = floorNodePath.posInterval(7, Point3(floorNodePath.getPos()),
                startPos=Point3(X - 5, Y, Z))
                PosInterval23 = floorNodePath.posInterval(7, Point3(X - 5, Y, Z),
                startPos=Point3(X + 5, Y, Z))

                self.movinStairs3 = Sequence(PosInterval13, PosInterval23, name="movinStairs3")
                self.movinStairs3.loop()

            y = y + 30
            z = z + 5


        # Coins
        X = 0
        Y = 175
        Z = 12
        self.collectableCoins(X, Y, Z, 0, 30, 2, 'Null', 0, 3)


        #########################################################
        #               FLOOR 2
        #########################################################
        shape = BulletBoxShape(Vec3(15,35,1))
        floorNode = BulletRigidBodyNode('Floor2')
        floorNode.addShape(shape)
        floorNodePath = self.render.attachNewNode(floorNode)
        floorNodePath.setCollideMask(BitMask32.allOn())
        floorNodePath.setPos(0, 325, 10)
        self.world.attachRigidBody(floorNodePath.node())
        floorModel = self.loader.loadModel("models/stone.egg")
        floorModel.setScale(30, 70, 1)
        floorModel.setPos(0, 0, 0)
        floorModel.reparentTo(floorNodePath)

        floorModel.setTexture(floorTexture, 1)

 	# normal-map texture for the plane
        self.normal = self.loader.loadTexture('coin-texture.jpg')#layingrock-n.jpg')
        self.ts = TextureStage('ts')
	self.ts.setMode(TextureStage.MNormal)

        floorModel.setTexture(self.ts, self.normal)
        floorModel.setShaderAuto()

        # Coins
        X = -2
        Y = 290
        Z = 18
        self.collectableCoins(X, Y, Z, 0, 15, 0, 'X', 2, 4)

        ###########################
        #      FLOOR STEPS 2
        ##########################
        y = 380
        z = 8
        x = 0
        for i in range(3):
            shape = BulletBoxShape(Vec3(5, 7.5, 1))
            floorNode = BulletRigidBodyNode('Floor')
            floorNode.addShape(shape)
            floorNodePath = self.render.attachNewNode(floorNode)
            floorNodePath.setCollideMask(BitMask32.allOn())
            floorNodePath.setPos(x, y, z)
            self.world.attachRigidBody(floorNodePath.node())
            floorModel = self.loader.loadModel("models/stone.egg")
            floorModel.setScale(10, 15, 1)
            #floorModel.setPos(0, 0, 0)
            floorModel.reparentTo(floorNodePath)

            floorModel.setTexture(floorTexture, 1)

            X, Y, Z = floorNodePath.getPos()

            if (i == 0) :
                PosInterval14 = floorNodePath.posInterval(7, Point3(X + 5, Y, Z),
                startPos=Point3(X - 5, Y, Z))
                PosInterval24 = floorNodePath.posInterval(7, Point3(X - 5, Y, Z),
                startPos=Point3(X + 5, Y, Z))

                self.movinStairs4 = Sequence(PosInterval14, PosInterval24, name="movinStairs4")
                self.movinStairs4.loop()
            if (i == 1) :
                PosInterval15 = floorNodePath.posInterval(7, Point3(floorNodePath.getPos()),
                startPos=Point3(X + 5, Y, Z))
                PosInterval25 = floorNodePath.posInterval(7, Point3(X + 5, Y, Z),
                startPos=Point3(X - 5, Y, Z))

                self.movinStairs5 = Sequence(PosInterval15, PosInterval25, name="movinStairs5")
                self.movinStairs5.loop()
            if (i == 2) :
                PosInterval16 = floorNodePath.posInterval(7, Point3(floorNodePath.getPos()),
                startPos=Point3(X - 5, Y, Z))
                PosInterval26 = floorNodePath.posInterval(7, Point3(X - 5, Y, Z),
                startPos=Point3(X + 5, Y, Z))

                self.movinStairs6 = Sequence(PosInterval16, PosInterval26, name="movinStairs6")
                self.movinStairs6.loop()

            y = y + 40
            z = z - 2

        ##########################################
        #           FLOOR 3
        ##########################################
        shape = BulletBoxShape(Vec3(10,100,1))
        floorNode = BulletRigidBodyNode('Floor')
        floorNode.addShape(shape)
        floorNodePath = self.render.attachNewNode(floorNode)
        floorNodePath.setCollideMask(BitMask32.allOn())
        floorNodePath.setPos(0, 600, 1)
        self.world.attachRigidBody(floorNodePath.node())
        floorModel = self.loader.loadModel("models/stone.egg")
        floorModel.setScale(20, 200, 1)
        floorModel.setPos(0, 0, 0)
        floorModel.reparentTo(floorNodePath)

        floorModel.setTexture(floorTexture, 1)

        # normal-map texture for the plane
        self.normal = self.loader.loadTexture('layingrock-n.jpg')
        self.ts = TextureStage('ts')
	self.ts.setMode(TextureStage.MNormal)

        floorModel.setTexture(self.ts, self.normal)
        floorModel.setShaderAuto()

        # Coins
        Y = 525
        Z = 12
        self.collectableCoins(X, Y, Z, 0, 12, 0, 'Z', 2, 3)

        ##########################################
        #           Rotating Disks
        ##########################################
        x = -5
        y = 750
        z = 2
        for i in range(3):
            # FLOOR with Circles
            #size = Vec3(0, 0, 1)
            #shape = BulletPlaneShape(Vec3(150,15,1))
            #shape = BulletSphereShape(5)
            shape = BulletBoxShape(Vec3(10, 10, 0.5))
            floorNode = BulletRigidBodyNode('Disk')
            floorNode.addShape(shape)
            floorNodePath = self.render.attachNewNode(floorNode)
            floorNodePath.setCollideMask(BitMask32.allOn())
            floorNodePath.setPos(x, y, z)
            self.world.attachRigidBody(floorNodePath.node())
            floorModel = self.loader.loadModel("models/disk.egg")
            floorModel.setScale(5,5,2)
            floorModel.setPos(0, 0, 0)
            floorModel.reparentTo(floorNodePath)

            ts = TextureStage.getDefault()
            texture = floorModel.getTexture()
            floorModel.setTexOffset(ts, 1, 1)
            floorModel.setTexScale(ts, 75, 75)

            floorTexture = self.loader.loadTexture("layingrock-c.jpg")#wood.png")
            floorModel.setTexture(floorTexture, 1)


            if(i==0):
                """
                HprInterval1 = floorNodePath.hprInterval(3, Point3(360, 0, 0), startHpr=Point3(0, 0, 0))

                self.movinDisk1 = Sequence(HprInterval1,  name="movinDisk1")
                self.movinDisk1.loop()
                """
                x = x + 10

            if(i==1):
                """
                HprInterval2 = floorNodePath.hprInterval(3, Point3(-360, 0, 0), startHpr=Point3(0, 0, 0))

                self.movinDisk2 = Sequence(HprInterval2,  name="movinDisk2")
                self.movinDisk2.loop()
                """
                x = x - 10

            if(i==2):
                """
                HprInterval3 = floorNodePath.hprInterval(3, Point3(360, 0, 0), startHpr=Point3(0, 0, 0))

                self.movinDisk3 = Sequence(HprInterval3,  name="movinDisk3")
                self.movinDisk3.loop()
                """

            y = y + 65

        # Coins
        Y = 750
        Z = 3
        X = -5.25
        for i in range(3):
            coinModel = self.loader.loadModel('models/box')
            coinModel.reparentTo(self.render)
            coinModel.setScale(2, 2, 2)
            coinModel.setPos(X, Y, Z)
            coinModel.setTag("coin", str(i))
            coin_tex = self.loader.loadTexture("models/coin.jpg")
            coinModel.setTexture(coin_tex, 1)
            Y = Y + 65
            if ( i%2 == 0 ): X = X + 10
            else : X = X - 10


        #################################################
        #               FLOOR 4
        #################################################
        shape = BulletBoxShape(Vec3(10,100,1))
        floorNode = BulletRigidBodyNode('Floor')
        floorNode.addShape(shape)
        floorNodePath = self.render.attachNewNode(floorNode)
        floorNodePath.setCollideMask(BitMask32.allOn())
        floorNodePath.setPos(0, 1040, 1)
        self.world.attachRigidBody(floorNodePath.node())
        floorModel = self.loader.loadModel("models/stone.egg")
        floorModel.setScale(20, 200, 1)
        floorModel.setPos(0, 0, 0)
        floorModel.reparentTo(floorNodePath)

        ts = TextureStage.getDefault()
        texture = floorModel.getTexture()
        floorModel.setTexOffset(ts, 1, 1)
        floorModel.setTexScale(ts, 50, 50)

        floorTexture = self.loader.loadTexture("layingrock-c.jpg")#wood.png")
        floorModel.setTexture(floorTexture, 1)
        #floorTexture.setWrapU(Texture.WMRepeat)
        #floorTexture.setWrapV(Texture.WMRepeat)

 	# normal-map texture for the plane
        self.normal = self.loader.loadTexture('coin-texture.jpg')#layingrock-n.jpg')
        self.ts = TextureStage('ts')
	self.ts.setMode(TextureStage.MNormal)

        floorModel.setTexture(self.ts, self.normal)
        floorModel.setShaderAuto()
        #print "x:",x, " y:",y, " z:",z


        ############################
        #           SPINNER 1
        ##########################
        h = 7.0
        w = 1.0
        shape = BulletCapsuleShape(w, h + 3 * w, ZUp)

        spinnerNode1 = BulletRigidBodyNode('Spinner1')
        spinnerNode1.addShape(shape)
        self.spinnerNodePath1 = self.render.attachNewNode(spinnerNode1)
        self.spinnerNodePath1.setCollideMask(BitMask32.allOn())
        self.spinnerNodePath1.setPos(0, 1015, 4)
        self.world.attachRigidBody(self.spinnerNodePath1.node())
        spinnerModel1 = self.loader.loadModel("models/spinner.egg")
        spinnerModel1.setScale(0.75)
        spinnerModel1.setPos(0, 0, 0)
        spinnerModel1.reparentTo(self.spinnerNodePath1)


















        #############################
        #          BEAM
        ##########################
        x = 0
        y = 1190
        z = 1
        for i in range(3):
            shape = BulletBoxShape(Vec3(7,5,1))
            #floorShape = BulletPlaneShape(Vec3(0, 0, 1), 0)
            floorNode = BulletRigidBodyNode('Floor')
            floorNode.addShape(shape)
            floorNodePath = self.render.attachNewNode(floorNode)
            floorNodePath.setCollideMask(BitMask32.allOn())
            floorNodePath.setPos(x, y, z)
            self.world.attachRigidBody(floorNodePath.node())
            floorModel = self.loader.loadModel("models/beam.egg")
            floorModel.setScale(0.5, 7, 1)
            floorModel.setPos(0, 0, 0)
            floorModel.reparentTo(floorNodePath)

            floorModel.setTexture(floorTexture, 1)

            y = y + 55

        #print "x:",x, " y:",y, " z:",z

        self.collectableCoins(0, 1160, 10, 0, 55, 0, 'Null', 0, 3)

        x = 0
        y = 1350
        z = 1


        ###############################
        #     Slant Boxes
        #############################
        self.createBox()

        #################################################
        #               FLOOR 2 - 2
        #################################################
        x = 0
        y = 1660
        z = -2
        shape = BulletBoxShape(Vec3(20,100,1))
        floorNode = BulletRigidBodyNode('Floor')
        floorNode.addShape(shape)
        floorNodePath = self.render.attachNewNode(floorNode)
        floorNodePath.setCollideMask(BitMask32.allOn())
        floorNodePath.setPos(x, y, z)
        self.world.attachRigidBody(floorNodePath.node())
        floorModel = self.loader.loadModel("models/stone.egg")
        floorModel.setScale(40, 200, 1)
        floorModel.setPos(0, 0, 0)
        floorModel.reparentTo(floorNodePath)

        ts = TextureStage.getDefault()
        texture = floorModel.getTexture()
        floorModel.setTexOffset(ts, 1, 1)
        floorModel.setTexScale(ts, 75, 75)

        floorTexture = self.loader.loadTexture("layingrock-c.jpg")#wood.png")
        floorModel.setTexture(floorTexture, 1)

 	# normal-map texture for the plane
        self.normal = self.loader.loadTexture('coin-texture.jpg')#layingrock-n.jpg')
        self.ts = TextureStage('ts')
	self.ts.setMode(TextureStage.MNormal)

        floorModel.setTexture(self.ts, self.normal)
        floorModel.setShaderAuto()

        ###################################
        #       FINAL FLOOR STEPS - 1
        ###################################
        y = 1790
        z = 1
        x = 0
        for i in range(3):
            shape = BulletBoxShape(Vec3(5, 7.5, 1))
            floorNode = BulletRigidBodyNode('Floor')
            floorNode.setMass(0)
            floorNode.addShape(shape)
            floorNodePath = self.render.attachNewNode(floorNode)
            floorNodePath.setCollideMask(BitMask32.allOn())
            floorNodePath.setPos(x, y, z)
            self.world.attachRigidBody(floorNodePath.node())
            floorModel = self.loader.loadModel("models/stone.egg")
            floorModel.setScale(10, 15, 1)
            floorModel.setPos(0, 0, 0)
            floorModel.reparentTo(floorNodePath)

            floorModel.setTexture(floorTexture, 1)

            X, Y, Z = floorNodePath.getPos()

            if (i == 0) :
                PosIntervalFinal1 = floorNodePath.posInterval(7, Point3(X + 5, Y, Z),
                startPos=Point3(X - 5, Y, Z))
                PosIntervalFinal2 = floorNodePath.posInterval(7, Point3(X - 5, Y, Z),
                startPos=Point3(X + 5, Y, Z))

                self.movinStairsFinal1 = Sequence(PosIntervalFinal1, PosIntervalFinal2, name="movinStairsFinal1")
                self.movinStairsFinal1.loop()
            if (i == 1) :
                PosIntervalFinal12 = floorNodePath.posInterval(7, Point3(floorNodePath.getPos()),
                startPos=Point3(X + 5, Y, Z))
                PosIntervalFinal22 = floorNodePath.posInterval(7, Point3(X + 5, Y, Z),
                startPos=Point3(X - 5, Y, Z))

                self.movinStairsFinal2 = Sequence(PosIntervalFinal12, PosIntervalFinal22, name="movinStairsFinal2")
                self.movinStairsFinal2.loop()
            if (i == 2) :
                PosIntervalFinal13 = floorNodePath.posInterval(7, Point3(floorNodePath.getPos()),
                startPos=Point3(X - 5, Y, Z))
                PosIntervalFinal23 = floorNodePath.posInterval(7, Point3(X - 5, Y, Z),
                startPos=Point3(X + 5, Y, Z))

                self.movinStairsFinal3 = Sequence(PosIntervalFinal13, PosIntervalFinal23, name="movinStairsFinal3")
                self.movinStairsFinal3.loop()

            y = y + 30
            z = z + 5

        # Coins
        X = 0
        Y = 1760
        Z = 9
        self.collectableCoins(X, Y, Z, 0, 40, 3, 'Null', 0, 3)


        #########################################################
        #          FINAL DESTINATION
        ######################################################
        shape = BulletBoxShape(Vec3(15,35,1))
        floorNode = BulletRigidBodyNode('Floor2')
        floorNode.addShape(shape)
        floorNodePath = self.render.attachNewNode(floorNode)
        floorNodePath.setCollideMask(BitMask32.allOn())
        floorNodePath.setPos(0, 1900, 14)
        self.world.attachRigidBody(floorNodePath.node())
        floorModel = self.loader.loadModel("models/stone.egg")
        floorModel.setScale(30, 70, 1)
        floorModel.setPos(0, 0, 0)
        floorModel.reparentTo(floorNodePath)

        floorModel.setTexture(floorTexture, 1)

 	# normal-map texture for the plane
        self.normal = self.loader.loadTexture('coin-texture.jpg')#layingrock-n.jpg')
        self.ts = TextureStage('ts')
	self.ts.setMode(TextureStage.MNormal)

        floorModel.setTexture(self.ts, self.normal)
        floorModel.setShaderAuto()

        ##############
        #   SPINNER 2
        ##############
        h = 10.0
        w = 1.0
        shape = BulletCapsuleShape(w, h + 3 * w, ZUp)

        spinnerNode2 = BulletRigidBodyNode('Spinner2')
        spinnerNode2.addShape(shape)
        spinnerNodePath2 = self.render.attachNewNode(spinnerNode2)
        spinnerNodePath2.setCollideMask(BitMask32.allOn())
        spinnerNodePath2.setPos(0, 1910, 21)
        self.world.attachRigidBody(spinnerNodePath2.node())
        spinnerModel2 = self.loader.loadModel("models/spinner.egg")
        spinnerModel2.setScale(0.75)
        spinnerModel2.setPos(0, 0, -5)
        spinnerModel2.reparentTo(spinnerNodePath2)



















        ###############################
        #      CHARACTER
        ################################
        h = 5.0
        w = 1.0
        shape = BulletCapsuleShape(w, h + 2 * w, ZUp)

        self.character = BulletCharacterControllerNode(shape, 0.7, 'Player')
        self.character.setGravity(15)
        #    self.character.setMass(1.0)
        self.characterNP = self.render.attachNewNode(self.character)
        self.characterNP.setPos(0, 0, 15)    # For Level 2: y = 1060
        self.characterNP.setH(0)
        self.characterNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.character)

        self.actorNP = Actor('models/robot/lack.egg', {
                 'run' : 'models/robot/lack-run.egg',
                 'damage' : 'models/robot/lack-damage.egg',
                 'idle' : 'models/robot/lack-idle.egg',
                 'jump' : 'models/robot/lack-jump.egg',
                 'land' : 'models/robot/lack-land.egg',
                 'tightrope' : 'models/robot/lack-tightrope.egg'})

        #modelname = "models/ralph"
        #self.actorNP = self.loader.loadModel("models/ralph")
        self.actorNP.reparentTo(self.characterNP)
        self.actorNP.setScale(.4)
        self.actorNP.setH(180)
        self.actorNP.setPos(0, 0, .5)

        ###############################
        #    BEEFY - THE ENEMY
        ################################
        h = 5.0
        w = 1.0
        shape = BulletCapsuleShape(w, h + 2 * w, ZUp)

        self.char = BulletCharacterControllerNode(shape, 0.7, 'Enemy')
        self.char.setGravity(15)
        #    self.char.setMass(1.0)
        self.charNP = self.render.attachNewNode(self.char)
        self.charNP.setPos(0, 625, 23)
        self.charNP.setH(0)
        self.charNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.char)

        self.enemyNP = Actor('Actors/beefy/beefy.egg', {
                 'walk' : 'Actors/beefy/beefy-walk.egg',
                 'idle' : 'Actors/beefy/beefy-idle.egg'})

        self.enemyNP.reparentTo(self.charNP)
        self.enemyNP.setScale(.4)
        self.enemyNP.setH(90)
        self.enemyNP.setPos(0, 0, .5)

        self.enemyNP.loop("walk")

        beefyPosInterval1 = self.charNP.posInterval(7, Point3(3, 625, 7),
        startPos=Point3(-3, 625, 7))
        beefyPosInterval2 = self.charNP.posInterval(7, Point3(-3, 625, 7),
        startPos=Point3(3, 625, 7))
        beefyHprInterval1 = self.charNP.hprInterval(1, Point3(180, 0, 0),
        startHpr=Point3(0, 0, 0))
        beefyHprInterval2 = self.charNP.hprInterval(1, Point3(0, 0, 0),
        startHpr=Point3(180, 0, 0))

        # Create and play the sequence that coordinates the intervals.
        self.beefyPos = Sequence(beefyPosInterval1, beefyHprInterval1, beefyPosInterval2, beefyHprInterval2, name="beefyPos")
        self.beefyPos.loop()

        """
        beefyHprInterval = self.charNP.hprInterval(1, Point3(360, 0, 0),
        startHpr=Point3(0, 0, 0))
        # Create and play the sequence that coordinates the intervals.
        self.rotateRalph = Sequence(beefyHprInterval, duration = 3,  name="rotateRalph")
        self.rotateRalph.loop()
        """


        ###############################
        #    BEEFY - THE ENEMY  22222222222222222
        ################################
        h = 5.0
        w = 1.0
        shape2 = BulletCapsuleShape(w, h + 2 * w, ZUp)

        self.char2 = BulletCharacterControllerNode(shape2, 0.7, 'Enemy2')
        self.char2.setGravity(15)
        #    self.char2.setMass(1.0)
        self.charNP2 = self.render.attachNewNode(self.char2)
        self.charNP2.setPos(0, 1700, 18)
        self.charNP2.setH(0)
        self.charNP2.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.char2)

        self.enemyNP2 = Actor('Actors/beefy/beefy.egg', {
                 'walk' : 'Actors/beefy/beefy-walk.egg',
                 'idle' : 'Actors/beefy/beefy-idle.egg'})

        self.enemyNP2.reparentTo(self.charNP2)
        self.enemyNP2.setScale(.4)
        self.enemyNP2.setH(90)
        self.enemyNP2.setPos(0, 0, .5)

        self.enemyNP2.loop("walk")

        beefyPosInterval21 = self.charNP2.posInterval(3, Point3(13, 1700, 3),
        startPos=Point3(-13, 1700, 3))
        beefyPosInterval22 = self.charNP2.posInterval(3, Point3(-13, 1700, 3),
        startPos=Point3(13, 1700, 3))
        beefyHprInterval21 = self.charNP2.hprInterval(0.5, Point3(180, 0, 0),
        startHpr=Point3(0, 0, 0))
        beefyHprInterval22 = self.charNP2.hprInterval(0.5, Point3(0, 0, 0),
        startHpr=Point3(180, 0, 0))

        # Create and play the sequence that coordinates the intervals.
        self.beefyPos2 = Sequence(beefyPosInterval21, beefyHprInterval21, beefyPosInterval22, beefyHprInterval22, name="beefyPos2")
        self.beefyPos2.loop()


        ###############################
        #    BEEFY - THE ENEMY  33333333333333333
        ################################
        h = 5.0
        w = 1.0
        shape3 = BulletCapsuleShape(w, h + 2 * w, ZUp)

        self.char3 = BulletCharacterControllerNode(shape3, 0.7, 'Enemy3')
        self.char3.setGravity(15)
        #    self.char2.setMass(1.0)
        self.charNP3 = self.render.attachNewNode(self.char3)
        self.charNP3.setPos(0, 1700, 18)
        self.charNP3.setH(0)
        self.charNP3.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.char3)

        self.enemyNP3 = Actor('Actors/beefy/beefy.egg', {
                 'walk' : 'Actors/beefy/beefy-walk.egg',
                 'idle' : 'Actors/beefy/beefy-idle.egg'})

        self.enemyNP3.reparentTo(self.charNP3)
        self.enemyNP3.setScale(.4)
        self.enemyNP3.setH(270)
        self.enemyNP3.setPos(0, 0, .5)

        self.enemyNP3.loop("walk")

        beefyPosInterval31 = self.charNP3.posInterval(3, Point3(-13, 1725, 3),
        startPos=Point3(13, 1725, 3))
        beefyPosInterval32 = self.charNP3.posInterval(3, Point3(13, 1725, 3),
        startPos=Point3(-13, 1725, 3))
        beefyHprInterval31 = self.charNP3.hprInterval(0.5, Point3(180, 0, 0),
        startHpr=Point3(0, 0, 0))
        beefyHprInterval32 = self.charNP3.hprInterval(0.5, Point3(0, 0, 0),
        startHpr=Point3(180, 0, 0))

        # Create and play the sequence that coordinates the intervals.
        self.beefyPos3 = Sequence(beefyPosInterval31, beefyHprInterval31, beefyPosInterval32, beefyHprInterval32, name="beefyPos3")
        self.beefyPos3.loop()


        ###############################
        #    BEEFY - THE ENEMY  444444444444444
        ################################
        h = 5.0
        w = 1.0
        shape4 = BulletCapsuleShape(w, h + 2 * w, ZUp)

        self.char4 = BulletCharacterControllerNode(shape4, 0.7, 'Enemy4')
        self.char4.setGravity(15)
        #    self.char2.setMass(1.0)
        self.charNP4 = self.render.attachNewNode(self.char4)
        self.charNP4.setPos(0, 1700, 18)
        self.charNP4.setH(0)
        self.charNP4.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.char4)

        self.enemyNP4 = Actor('Actors/beefy/beefy.egg', {
                 'walk' : 'Actors/beefy/beefy-walk.egg',
                 'idle' : 'Actors/beefy/beefy-idle.egg'})

        self.enemyNP4.reparentTo(self.charNP4)
        self.enemyNP4.setScale(.4)
        self.enemyNP4.setH(270)
        self.enemyNP4.setPos(0, 0, .5)

        self.enemyNP4.loop("walk")

        beefyPosInterval41 = self.charNP4.posInterval(3, Point3(-13, 1675, 3),
        startPos=Point3(13, 1675, 3))
        beefyPosInterval42 = self.charNP4.posInterval(3, Point3(13, 1675, 3),
        startPos=Point3(-13, 1675, 3))
        beefyHprInterval41 = self.charNP4.hprInterval(0.5, Point3(180, 0, 0),
        startHpr=Point3(0, 0, 0))
        beefyHprInterval42 = self.charNP4.hprInterval(0.5, Point3(0, 0, 0),
        startHpr=Point3(180, 0, 0))

        # Create and play the sequence that coordinates the intervals.
        self.beefyPos4 = Sequence(beefyPosInterval41, beefyHprInterval41, beefyPosInterval42, beefyHprInterval42, name="beefyPos4")
        self.beefyPos4.loop()

        ##########################################
        #    RALPHIE - RALPH'S GIRLFRIEND
        #######################################
        # Character
        h = 7
        w = 1.2
        shape5 = BulletCapsuleShape(w, h - 2 * w, ZUp)

        self.character5 = BulletCharacterControllerNode(shape5, 0.4, 'Ralphie')
        #    self.character.setMass(1.0)
        self.characterNP5 = self.render.attachNewNode(self.character5)
        self.characterNP5.setPos(-2, 1908, 18)
        self.characterNP5.setH(0)
        self.characterNP5.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.character5)

        self.actorNP5 = Actor('models/ralph/ralph.egg', {
                         'run' : 'models/ralph/ralph-run.egg',
                         'walk' : 'models/ralph/ralph-walk.egg',
                         'jump' : 'models/ralph/ralph-jump.egg'})

        self.actorNP5.reparentTo(self.characterNP5)
        self.actorNP5.setScale(1.5)
        self.actorNP5.setH(0)
        self.actorNP5.setPos(0, 0, -4)

game = CharacterController()
game.run()
