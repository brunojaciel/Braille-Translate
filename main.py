import sys
import numpy as np
import cv2
import mouse

def capturePhoto():
    # Tirar foto com camara

    cap = cv2.VideoCapture(0)
    i=1

    while(cv2.waitKey(5)-27 and i==1):
        _, fr=cap.read()
        fr=cv2.resize(fr,(600,300),interpolation=cv2.INTER_AREA)
        if mouse.is_pressed(button="right"):
            cv2.imwrite("Frame.jpg", fr)
            i=0
            print("Tirou foto")
        cv2.imshow("Janela A", fr)

    cap.release()
    cv2.destroyAllWindows()

def filtrar_imagem(file):
    imageBraille = cv2.imread(file)
    ans = imageBraille.copy()
    gray = cv2.cvtColor(imageBraille, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((5, 5), np.uint8)
    img = cv2.medianBlur(gray, 5)
    cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 19, 2)
    test = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 19, 2)
    test = cv2.erode(test, kernel)
    test = cv2.dilate(test, kernel)

    cv2.imshow("imagemOriginal", ans)
    cv2.imshow("Result", test)
    return test

def histograma_acumulativo(file):
    test=filtrar_imagem(file)

    height, width = test.shape[:2]
    histH = []
    for c in range(width):
        conta = 0
        for l in range(height):
            conta += test[l, c]
        histH.append(conta / height)

    histV = []
    for l in range(height):
        conta = 0
        for c in range(width):
            conta += test[l, c]
        histV.append(conta / width)

    aux = 1
    sizeHeight = []
    for l in range(height):
        if (histV[l - 1] == 0):
            aux = 0
        if (histV[l - 1] > histV[l] and aux == 0):
            sizeHeight.append(l - 1)
            aux = 1

    aux = 1
    sizeWidth = []
    for c in range(width):
        if (histH[c - 1] == 0):
            aux = 0
        if (histH[c - 1] > histH[c] and aux == 0):
            sizeWidth.append(c - 1)
            aux = 1

    HH = np.zeros((101,width,3), np.uint8)
    for c in range(width):
        cv2.line(HH, (c, 100-int(histH[c]*100/255)), (c, 100), (0,0,255))
    cv2.imshow('HH', HH)

    HV = np.zeros((height, 101, 3), np.uint8)
    for l in range(height):
        cv2.line(HV, (int(histV[l]*100/255), l), (0, l), (0, 255, 0))
    cv2.imshow('HV', HV)

    return sizeWidth, sizeHeight,height, width

def get_frase(file):
    # Recebe os vetores do histograma e imagem com filtro
    sizeWidth, sizeHeight, height, width = histograma_acumulativo(file)
    thresh = filtrar_imagem(file)

    arrayTextBytes = []
    auxLine = True
    auxColumn = True
    firstLine = True

    wordByte = 0x00

    # print("tamanho array altura: ", len(sizeHeight))
    # print("tamanho array largura: ", len(sizeWidth))

    #Caso falte algum ponto nas linhas
    differenceHeight = []
    if (len(sizeHeight) % 3) != 0:

        for i in range(0, len(sizeHeight) - 1):
            x1 = sizeHeight[i]
            x2 = sizeHeight[i + 1]
            x3 = x2 - x1
            differenceHeight.append(x3)
        #print("Diferença Largura:",differenceHeight)

    # Caso falte algum ponto nas colunas
    differenceWidth = []
    if (len(sizeWidth) % 2) != 0:

        for i in range(0, len(sizeWidth) - 1):
            x1 = sizeWidth[i]
            x2 = sizeWidth[i + 1]
            x3 = x2 - x1
            differenceWidth.append(x3)
        #print("Diferença Altura:", differenceWidth)

    #insere a posicao no qual falta o ponto no vetor do histograma
    if (len(differenceWidth) != 0):
        for y in range(0, len(sizeWidth)):
            if ((sizeWidth[y + 1] - sizeWidth[y]) + 10 > max(differenceWidth)):
                sizeWidth.insert(y+1, sizeWidth[y] + min(differenceWidth))

    if (len(differenceHeight) != 0):
        for y in range(0, len(sizeHeight)):
            if ((sizeHeight[y + 1] - sizeHeight[y]) + 10 > max(differenceHeight)):
                sizeHeight.insert(y+1, sizeHeight[y] + min(differenceHeight))

    #print("Width:", sizeWidth)
    #print("Height:", sizeHeight)


    # Transformando as cordenadas em valores (Processamento)
    for i in range(3, len(sizeHeight) + 1, 3):
        auxLine = not auxLine
        for j in range(2, len(sizeWidth) + 1, 2):
            auxi = i
            auxj = j
            for x in range(auxi - 3, i):
                auxColumn = True
                firstLine = True
                for y in range(auxj - 2, j):
                    # Primeira coluna False, Segunda coluna True
                    auxColumn = not auxColumn
                    # Verificar se é a primeira linha ou a terceira
                    if (x - (auxi - 1) == 0):
                        firstLine = False
                    if (thresh[sizeHeight[x], sizeWidth[y]] == 255 and (
                            y + 1) % 2 != 0 and auxColumn == False and firstLine == True) and (
                            auxLine == False and (x + 1) % 2 != 0 or auxLine == True and x % 2 != 0):
                        wordByte += 0x20
                    if (thresh[sizeHeight[x], sizeWidth[y]] == 255 and (
                            y + 1) % 2 != 0 and auxColumn == False and firstLine == False) and (
                            auxLine == False and (x + 1) % 2 != 0 or auxLine == True and x % 2 != 0):
                        wordByte += 0x02
                    if (thresh[sizeHeight[x], sizeWidth[y]] == 255 and (
                            y + 1) % 2 == 0 and auxColumn == True and firstLine == True) and (
                            auxLine == False and (x + 1) % 2 != 0 or auxLine == True and x % 2 != 0):
                        wordByte += 0x10
                    if (thresh[sizeHeight[x], sizeWidth[y]] == 255 and (
                            y + 1) % 2 == 0 and auxColumn == True and firstLine == False) and (
                            auxLine == False and (x + 1) % 2 != 0 or auxLine == True and x % 2 != 0):
                        wordByte += 0x01
                    if (thresh[sizeHeight[x], sizeWidth[y]] == 255 and (y + 1) % 2 != 0) and (
                            auxLine == False and (x + 1) % 2 == 0 or auxLine == True and x % 2 == 0):
                        wordByte += 0x08
                    if (thresh[sizeHeight[x], sizeWidth[y]] == 255 and (y + 1) % 2 == 0) and (
                            auxLine == False and (x + 1) % 2 == 0 or auxLine == True and x % 2 == 0):
                        wordByte += 0x04

            #Insere a palavra
            arrayTextBytes.append(wordByte)
            wordByte = 0x00
        # Para quebrar linhas
        arrayTextBytes.append(0x00)


    #print("Letras: ", arrayTextBytes)

    # Dicionario
    dictionaryByte = [0x20, 0x28, 0x30, 0x34, 0x24, 0x38, 0x3c, 0x2c, 0x18, 0x1c, 0x22, 0x2a, 0x32, 0x36, 0x26, 0x3a,
                      0x7e, 0x2e, 0x1a, 0x1e, 0x23, 0x2b, 0x1d, 0x33, 0x37, 0x27]

    wordASCI = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']

    arrayTextTranslate = []

    #Traduzir as palavras
    for i in range(len(arrayTextBytes)):
        for j in range(len(dictionaryByte)):
            if arrayTextBytes[i] == dictionaryByte[j]:
                arrayTextTranslate.append(wordASCI[j])
            elif arrayTextBytes[i] == 0:
                arrayTextTranslate.append(" ")

    #Transformar em string e tirar os espacos a mais
    stringText = ''.join(arrayTextTranslate)
    stringText = " ".join(stringText.split())

    print(stringText)

def menu():
    print("************Welcome to Best Guys Software!**************")
    print()

    choice = input("""
                      A: Process de image
                      B: Take the picture and process
                      Q: Exit

                      Please enter your choice: """)

    if choice == "A" or choice =="a":
        file = input("Put the name of file:")
        get_frase(file)
    elif choice == "B" or choice =="b":
        image = capturePhoto()
        get_frase('Frame.jpg')
    elif choice=="Q" or choice=="q":
        sys.exit()
    else:
        print("You must only select either A or B")
        print("Please try again")
        menu()

menu()
cv2.waitKey(0)